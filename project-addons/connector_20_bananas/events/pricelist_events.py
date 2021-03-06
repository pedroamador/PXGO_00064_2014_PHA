# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import requests
from openerp.addons.connector.event import (
    on_record_create,
    on_record_unlink,
    on_record_write,
)
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Exporter

from ..backend import bananas
from ..unit.backend_adapter import GenericAdapter
from .utils import _get_exporter, get_next_execution_time


@bananas
class PartnerPricelistExporter(Exporter):

    _model_name = ["product.pricelist.custom.partner"]

    def insert(self, partner_id, pricelist_id, mode):
        vals = {"codtarifa": pricelist_id, "codcliente": partner_id}
        return self.backend_adapter.insert(vals)

    def delete(self, vals):
        self.backend_adapter.clean_whitelist(vals["codcliente"])
        return self.backend_adapter.remove_vals(vals)

    def insert_whitelist_item(self, partner_id, product_id):
        if not self.backend_adapter.check_id('{}/{}'.format(partner_id, product_id), 'listablanca'):
            self.backend_adapter.insert_whitelist(
                {"codcliente": partner_id, "codproducto": product_id}
            )

    def remove_whitelist_item(self, partner_id, product_id):
        self.backend_adapter.remove_whitelist(partner_id, product_id)

    def clean_whitelist(self, partner_id):
        self.backend_adapter.clean_whitelist(partner_id)


@bananas
class PartnerPricelistAdapter(GenericAdapter):
    _model_name = "product.pricelist.custom.partner"
    _bananas_model = "tarifasXclientes"
    _delete_id_in_url = False


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def export_partner_pricelist(session, model_name, record_id):
    partner_pricelist_exporter = _get_exporter(
        session,
        "product.pricelist.custom.partner",
        record_id,
        PartnerPricelistExporter,
    )
    partner = session.env[model_name].browse(record_id)
    partner_pricelist_exporter.clean_whitelist(partner.bananas_id)
    for item in partner.get_bananas_pricelist_items():
        if item.bananas_price > 0.0:
            partner_pricelist_exporter.insert_whitelist_item(
                partner.bananas_id, item.product_id.id
            )
    return partner_pricelist_exporter.insert(
        partner.bananas_id, partner.get_bananas_pricelist().bananas_id, "insert"
    )


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def unlink_partner_pricelist(session, model_name, record_id):
    partner_pricelist_exporter = _get_exporter(
        session,
        "product.pricelist.custom.partner",
        record_id,
        PartnerPricelistExporter,
    )
    partner = session.env[model_name].browse(record_id)
    backend = partner_pricelist_exporter.backend_record
    url = "%s/%s/*/%s" % (
        backend.location,
        "tarifasXclientes",
        partner.bananas_id,
    )
    headers = {"apikey": backend.api_key, "Content-Type": "application/json"}
    result = requests.request("GET", url, headers=headers)
    records = result.json()["records"]
    pricelist = partner.get_bananas_pricelist()
    if pricelist._name == "product.pricelist.custom.partner":
        pricelist.write({"active": False})

    if records:
        for record in records:
            partner_pricelist_exporter.delete(record)
    return


@bananas
class PricelistExporter(Exporter):

    _model_name = ["bananas.pricelist"]

    def insert(self, binding_id, mode):
        partner = self.env["res.partner"].browse(binding_id)
        pricelist = partner.get_bananas_pricelist()
        vals = {"codtarifa": pricelist.bananas_id}
        if pricelist._name == "product.pricelist.custom.partner":
            vals["descripcion"] = partner.name
        else:
            vals["descripcion"] = pricelist.name
        if not self.backend_adapter.check_id(vals['codtarifa']):
            return self.backend_adapter.insert(vals)

    def delete(self, binding_id):
        partner = self.env["res.partner"].browse(binding_id)
        pricelist = partner.get_bananas_pricelist()
        return self.backend_adapter.remove(pricelist.id)


@bananas
class PricelistAdapter(GenericAdapter):
    _model_name = "bananas.pricelist"
    _bananas_model = "tarifas"


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def export_pricelist(session, model_name, record_id):
    pricelist_exporter = _get_exporter(
        session, "bananas.pricelist", record_id, PricelistExporter
    )
    return pricelist_exporter.insert(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def unlink_pricelist(session, model_name, record_id):
    pricelist_exporter = _get_exporter(
        session, "bananas.pricelist", record_id, PricelistExporter
    )
    return pricelist_exporter.delete(record_id)


@bananas
class CustomerRateExporter(Exporter):

    _model_name = ["product.pricelist.custom.partner.item"]

    def update(self, binding_id, mode):
        customer_rate = self.model.browse(binding_id)
        vals = {
            "codtarifa": customer_rate.pricelist_id.bananas_id,
            "referencia": customer_rate.product_id.id,
            "precio": customer_rate.price,
        }
        if mode == "insert":
            if vals['precio'] > 0.0:
                self.backend_adapter.insert(vals)
        else:
            self.backend_adapter.update(binding_id, vals)

    def delete(self, data):
        self.backend_adapter.remove_vals(data)

    def insert_whitelist_item(self, partner_id, product_id):
        if not self.backend_adapter.check_id('{}/{}'.format(partner_id, product_id), 'listablanca'):
            self.backend_adapter.insert_whitelist(
                {"codcliente": partner_id, "codproducto": product_id}
            )

    def remove_whitelist_item(self, partner_id, product_id):
        self.backend_adapter.remove_whitelist(partner_id, product_id)

@bananas
class CustomerRateAdapter(GenericAdapter):
    _model_name = "product.pricelist.custom.partner.item"
    _bananas_model = "tarifasXarticulos"


@bananas
class CustomerRateExporter2(Exporter):

    _model_name = ["product.pricelist.item"]

    def update(self, binding_id, mode):
        customer_rate = self.model.browse(binding_id)
        vals = {
            "codtarifa": customer_rate.price_version_id.pricelist_id.bananas_id,
            "referencia": customer_rate.product_id.id,
            "precio": customer_rate.bananas_price,
        }
        if mode == "insert":
            if not self.backend_adapter.check_id('{}/{}'.format(vals['codtarifa'], vals['referencia'])):
                self.backend_adapter.insert(vals)
        else:
            self.backend_adapter.update(binding_id, vals)

    def delete(self, data):
        self.backend_adapter.remove_vals(data)

    def insert_whitelist_item(self, partner_id, product_id):
        if not self.backend_adapter.check_id('{}/{}'.format(partner_id, product_id), 'listablanca'):
            self.backend_adapter.insert_whitelist(
                {"codcliente": partner_id, "codproducto": product_id}
            )

    def remove_whitelist_item(self, partner_id, product_id):
        self.backend_adapter.remove_whitelist(partner_id, product_id)


@bananas
class CustomerRateAdapter2(GenericAdapter):
    _model_name = "product.pricelist.item"
    _bananas_model = "tarifasXarticulos"


@on_record_create(
    model_names=[
        "product.pricelist.custom.partner.item",
        "product.pricelist.item",
    ]
)
def delay_export_customer_rate_create(session, model_name, record_id, vals):
    rec = session.env[model_name].browse(record_id)
    eta = get_next_execution_time(session)
    if model_name == "product.pricelist.custom.partner.item":
        if not rec.pricelist_id.bananas_synchronized:
            return
    else:
        if not rec.price_version_id.pricelist_id.bananas_synchronized:
            return
    if not rec.product_id.bananas_synchronized:
        rec.product_id.bananas_synchronized = True
    if model_name == "product.pricelist.custom.partner.item":
        eta = get_next_execution_time(session)
        export_customer_rate.delay(
            session, model_name, record_id, priority=20, eta=eta+200
        )
        if not rec.pricelist_id.partner_id.partner_pricelist_exported:
            insert_whitelist_item_job.delay(
                session,
                model_name,
                record_id,
                rec.pricelist_id.partner_id.bananas_id,
                rec.product_id.id,
                priority=3,
                eta=eta+90,
            )
    else:
        if rec.price_version_id.pricelist_id.bananas_synchronized:
            export_customer_rate.delay(
                session, model_name, record_id, priority=20, eta=eta+200
            )
        partners = session.env["res.partner"].search(
            [
                ("property_product_pricelist", "=", rec.price_version_id.pricelist_id.id),
                ("bananas_synchronized", "=", True),
                ("commercial_discount", "=", 0),
                ("financial_discount", "=", 0),
            ]
        )
        for partner in partners:
            insert_whitelist_item_job.delay(
                session,
                model_name,
                record_id,
                partner.bananas_id,
                rec.product_id.id,
                priority=3,
                eta=eta+90,
            )


@on_record_write(
    model_names=[
        "product.pricelist.custom.partner.item",
        "product.pricelist.item",
    ]
)
def delay_export_customer_rate_write(session, model_name, record_id, vals):
    eta = get_next_execution_time(session)
    update_customer_rate.delay(
        session, model_name, record_id, priority=20, eta=eta+200
    )


@on_record_unlink(
    model_names=[
        "product.pricelist.custom.partner.item",
        "product.pricelist.item",
    ]
)
def delay_unlink_customer_rate(session, model_name, record_id):
    rate = session.env[model_name].browse(record_id)
    eta = get_next_execution_time(session)
    if model_name == "product.pricelist.custom.partner.item":
        data = {
            "codtarifa": rate.pricelist_id.bananas_id,
            "referencia": rate.product_id.id,
        }

        remove_whitelist_item_job.delay(
            session,
            model_name,
            record_id,
            [rate.pricelist_id.partner_id.bananas_id],
            rate.product_id.id,
            priority=3,
            eta=eta+90,
        )
    else:
        data = {
            "codtarifa": rate.price_version_id.pricelist_id.bananas_id,
            "referencia": rate.product_id.id,
        }

        partners = session.env["res.partner"].search(
            [
                ("property_product_pricelist", "=", rate.price_version_id.pricelist_id.id),
                ("bananas_synchronized", "=", True),
                ("commercial_discount", "=", 0),
                ("financial_discount", "=", 0),
            ]
        )
        remove_whitelist_item_job.delay(
            session,
            model_name,
            record_id,
            [x.bananas_id for x in partners],
            rate.product_id.id,
            priority=3,
            eta=eta+90,
        )
    unlink_customer_rate.delay(
        session, model_name, record_id, data=data, priority=1, eta=eta
    )


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def export_customer_rate(session, model_name, record_id):
    if model_name == "product.pricelist.custom.partner.item":
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter
        )
    else:
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter2
        )
    return customer_rate_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def insert_whitelist_item_job(
    session, model_name, record_id, partner_id, product_id
):
    if model_name == "product.pricelist.custom.partner.item":
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter
        )
    else:
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter2
        )
    customer_rate_exporter.insert_whitelist_item(partner_id, product_id)

@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def remove_whitelist_item_job(
    session, model_name, record_id, partner_id, product_id
):
    if model_name == "product.pricelist.custom.partner.item":
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter
        )
    else:
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter2
        )
    customer_rate_exporter.remove_whitelist_item(partner_id, product_id)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def update_customer_rate(session, model_name, record_id):
    if model_name == "product.pricelist.custom.partner.item":
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter
        )
    else:
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter2
        )
    return customer_rate_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def unlink_customer_rate(session, model_name, record_id, data):
    if model_name == "product.pricelist.custom.partner.item":
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter
        )
    else:
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter2
        )
    return customer_rate_exporter.delete(data)
