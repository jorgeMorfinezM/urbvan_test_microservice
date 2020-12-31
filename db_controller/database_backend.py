# -*- coding: utf-8 -*-
"""
Requires Python 3.8 or later
"""

__author__ = "Jorge Morfinez Mojica (jorge.morfinez.m@gmail.com)"
__copyright__ = "Copyright 2020, Jorge Morfinez Mojica"
__license__ = ""
__history__ = """ """
__version__ = "1.1.L31.2 ($Rev: 10 $)"

"""Oracle DB backend (db-oracle).

Each one of the CRUD operations should be able to open a database connection if
there isn't already one available (check if there are any issues with this).

Documentation:

"""

from sqlalchemy import create_engine, Column, Integer, String, Numeric
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import TimeoutError
from sqlalchemy.exc import InternalError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from db_controller import mvc_exceptions as mvc_exc
from constants.constants import Constants as Const
from logger_controller.logger_control import *
import psycopg2
from datetime import datetime
import json

import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

Base = declarative_base()
logger = configure_db_logger()


# Datos de conecxion a base de datos
def init_connect_db():
    r"""
    Contiene la inicializacion de datos para conectar a base de datos.
    :return: list_data_cnx
    """
    init_cnx_db_data = []

    cfg = get_config_constant_file()

    # TEST:
    db_host = cfg['DB_RDS']['HOST_DB']
    db_username = cfg['DB_RDS']['USER_DB']
    db_password = cfg['DB_RDS']['PASSWORD_DB']
    db_port = cfg['DB_RDS']['PORT_DB']
    db_driver = cfg['DB_RDS']['SQL_DRIVER']
    db_name = cfg['DB_RDS']['DATABASE_NAME']

    data_connection = [db_host, db_username, db_password, db_port, db_name]

    init_cnx_db_data.append(data_connection)

    return data_connection


def session_to_db():
    data_bd_connection = init_connect_db()

    connection = None

    try:

        if data_bd_connection:

            connection = psycopg2.connect(user=data_bd_connection[1],
                                          password=data_bd_connection[2],
                                          host=data_bd_connection[0],
                                          port=data_bd_connection[3],
                                          database=data_bd_connection[4])

        else:
            logger.error('Some data is not established to connect PostgreSQL DB. Please verify it!')

    except (Exception, psycopg2.Error) as error:
        logger.exception('Can not connect to database, verify data connection to %s', data_bd_connection[4],
                         error, exc_info=True)
        raise mvc_exc.ConnectionError(
            '"{}" Can not connect to database, verify data connection to "{}".\nOriginal Exception raised: {}'.format(
                data_bd_connection[0], data_bd_connection[4], error
            )
        )

    return connection


def scrub(input_string):
    """Clean an input string (to prevent SQL injection).

    Parameters
    ----------
    input_string : str

    Returns
    -------
    str
    """
    return "".join(k for k in input_string if k.isalnum())


def create_cursor(conn):
    try:
        cursor = conn.cursor()

    except (Exception, psycopg2.Error) as error:
        logger.exception('Can not create the cursor object, verify database connection', error, exc_info=True)
        raise mvc_exc.ConnectionError(
            'Can not connect to database, verify data connection.\nOriginal Exception raised: {}'.format(
                error
            )
        )

    return cursor


def disconnect_from_db_postgre(conn):
    if conn is not None:
        conn.close()


def close_cursor_postgre(cursor):
    if cursor is not None:
        cursor.close()


def disconnect_from_db(session):
    if session is not None:
        session.close()


def get_systimestamp_date(session):
    last_updated_date_column = session.execute('SELECT systimestamp from dual').scalar()

    logger.info('Timestamp from DUAL: %s', last_updated_date_column)

    return last_updated_date_column


def get_datenow_from_db(conn):
    last_updated_date = None

    sql_nowdate = 'SELECT now()'

    cursor = create_cursor(conn)

    cursor.execute(sql_nowdate)

    result = cursor.fetchall()

    if result is not None:
        last_updated_date = result

    cursor.close()

    return last_updated_date


def exists_data_row(session, table_name, column_name, column_filter1, value1, column_filter2, value2):
    # value1 = scrub(value1)
    # value2 = scrub(value2)

    # Column_validate = brand
    # table_name = tv_int_marcas_ofix_v
    # column_filter1 = integracion_id
    # value1 = 2
    # column_filter2 = marca_id
    # value2 = '102'

    row_data = None

    sql_exists = f"SELECT {column_name} FROM {table_name} " \
                 f"WHERE {column_filter1} = {value1} AND {column_filter2} = '{value2}'"

    # sql_exists = ("SELECT %(column_name)s "
    #               "FROM %(table_name)s "
    #               "WHERE %(column_filter1)s=%(value1)s AND %(column_filter2)s=%(value2)s",
    #               dict(column_name=column_name, table_name=table_name, column_filter1=column_filter1, value1=value1,
    #                    column_filter2=column_filter2, value2=value2))

    row_exists = session.execute(sql_exists)

    for r_e in row_exists:

        logger.info('Row Info in Query: %s', str(r_e))

        if r_e is None:
            r_e = None
        else:
            row_data = r_e[column_name]

        row_exists.close()

        return row_data


def exists_data_row_item(session, table_name,
                         column_name,
                         column_filter1, value1,
                         column_filter2, value2,
                         column_filter3, value3):
    # value1 = scrub(value1)
    # value2 = scrub(value2)

    # Column_validate = brand
    # table_name = tv_int_marcas_ofix_v
    # column_filter1 = integracion_id
    # value1 = 2
    # column_filter2 = marca_id
    # value2 = '102'

    row_data = None

    sql_exists = 'SELECT {} FROM {} WHERE {} = {} AND {} = {} AND {} = {}'.format(column_name, table_name,
                                                                                  column_filter1, value1,
                                                                                  column_filter2, "'" + value2 + "'",
                                                                                  column_filter3, "'" + value3 + "'")

    # sql_exists = ("SELECT %(column_name)s "
    #               "FROM %(table_name)s "
    #               "WHERE %(column_filter1)s = %(value1)s "
    #               "AND %(column_filter2)s = %(value2)s "
    #               "AND %(column_filter3)s = %(value3)s",
    #               dict(column_name=column_name, table_name=table_name, column_filter1=column_filter1, value1=value1,
    #                    column_filter2=column_filter2, value2=value2, column_filter3=column_filter3, value3=value3))

    row_exists = session.execute(sql_exists)

    for r_e in row_exists:

        logger.info('Row Info in Query: %s', str(r_e))

        if r_e is None:
            r_e = None
        else:
            row_data = r_e[column_name]

        row_exists.close()

        return row_data


def get_order_line_additional_data(session, table_name1, table_name2, tienda_virtual_id, sku):

    order_data_line = {}

    data_lines_order = {}

    try:

        sql_additional_data = ' SELECT si.sku_base, ' \
                              '        si.numero_articulo_fabricante, ' \
                              '        si.inventory_item_id, ' \
                              '        si.primary_uom_code uom, ' \
                              '        si.tax_code, ' \
                              '        tvo.vendor_id, ' \
                              '        claveprodserv, ' \
                              '        claveunidad, ' \
                              '        cveimpuesto, ' \
                              '        tipofactor, ' \
                              '        tasaocuota, ' \
                              '        gtin ' \
                              ' FROM {} si, ' \
                              '      {} tvo ' \
                              ' WHERE si.sku = {} ' \
                              ' AND tvo.tienda_virtual_id = {}'.format(table_name1,
                                                                       table_name2,
                                                                       "'" + sku + "'",
                                                                       tienda_virtual_id)

        data_line = session.execute(sql_additional_data)

        for d_l in data_line:
            if d_l is not None:

                sku = d_l['sku_base']
                manufacturer_part_number = d_l['numero_articulo_fabricante']
                inventory_item_id = d_l['inventory_item_id']
                unit_of_measure = d_l['uom']
                tax_code = d_l['tax_code']
                vendor_id = d_l['vendor_id']
                claveprod_sat = d_l['claveprodserv']
                claveunidad_sat = d_l['claveunidad']
                cveimpuesto_sat = d_l['cveimpuesto']
                tipofactor_sat = d_l['tipofactor']
                tasaocuota_sat = d_l['tasaocuota']
                product_id = d_l['gtin']

                order_data_line = {
                    "OrderDataLine": {
                        "Sku": sku,
                        "ManufacturerPartNumber": manufacturer_part_number,
                        "InventoryItemId": inventory_item_id,
                        "UOM": unit_of_measure,
                        "TaxCode": tax_code,
                        "VendorId": vendor_id,
                        "ClaveProducto": claveprod_sat,
                        "ClaveUnidad": claveunidad_sat,
                        "ClaveImpuesto": cveimpuesto_sat,
                        "TipoFactor": tipofactor_sat,
                        "TasaOCuota": tasaocuota_sat,
                        "ProductId": product_id
                    }
                }

            else:
                logger.error('Can not read the recordset, beacause is not stored')

                order_data_line = {
                    "OrderDataLine": {
                        "Sku": sku,
                        "ManufacturerPartNumber": ' ',
                        "InventoryItemId": '0',
                        "UOM": ' ',
                        "TaxCode": ' ',
                        "VendorId": '-1',
                        "ClaveProducto": ' ',
                        "ClaveUnidad": ' ',
                        "ClaveImpuesto": ' ',
                        "TipoFactor": ' ',
                        "TasaOCuota": ' ',
                        "ProductId": ' '
                    }
                }

                raise SQLAlchemyError(
                    "Can\'t read data because it\'s not stored in table {}, SQL Exception".format(table_name1)
                )

        data_lines_order = json.dumps(order_data_line)

        data_line.close()

    except SQLAlchemyError as sql_exc:
        logger.exception(sql_exc)
    # finally:
    #    session.close()

    return data_lines_order


class OrderDetail(Base):
    cfg = get_config_constant_file()

    __tablename__ = cfg['DB_ORACLE_OBJECTS']['ORDER_L']

    tipo_pedido = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['TIPO_PEDIDO'], String, primary_key=True)
    order_id = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['ORDER_ID'], Numeric, primary_key=True)
    order_item_guid = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['ORDER_ITEM_GUID'], String)
    product_id = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['PRODUCT_ID'], Numeric)
    product_name = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['PRODUCT_NAME'], String)
    sku = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['SKU'], String, primary_key=True)
    manufacturer_part_number = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['MANUFACTURER_PARTNUMBER'], String)
    vendor_id = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['VENDOR_ID'], Numeric)
    unit_price_incl_tax = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['UNITPRICE_INC_TAX'], Numeric)
    unit_price_excl_tax = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['UNITPRICE_EXC_TAX'], Numeric)
    price_incl_tax = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['PRICE_INC_TAX'], Numeric)
    price_excl_tax = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['PRICE_EXC_TAX'], Numeric)
    quantity = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['QUANTITY'], Numeric)
    discount_amount_incl_tax = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['DISCOUNT_AMOUNT_INC_TAX'], Numeric)
    discount_amount_excl_tax = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['DISCOUNT_AMOUNT_EXC_TAX'], Numeric)
    created_by = Column(cfg['DB_COLUMNS_DATA']['USER_ID'], Numeric)
    last_updated_by = Column(cfg['DB_COLUMNS_DATA']['USER_UPD_ID'], Numeric)
    uom = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['UNIT_OF_MEASURE'], String)
    line_number = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['LINE_NUMBER'], Numeric)
    inventory_item = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['INVENTORY_ITEM'], String)
    inventory_item_id = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['INVENTORY_ITEM_ID'], Numeric)
    tax_code = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['TAX_CODE'], String)
    status_item = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['STATUS_ITEM'], String)
    item_comment = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['ITEM_COMMENTS'], String)
    agreement_item = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['AGREEMENT_ITEM'], String)
    clave_prod_serv_sat = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['CLAVE_PRODUCTO_SERV'], String)
    clave_unidad_sat = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['CLAVE_UNIDAD'], String)
    clave_impuesto_sat = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['CLAVE_IMPUESTO'], String)
    tipo_factor_sat = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['TIPO_FACTOR'], String)
    tasaocuota_sat = Column(cfg['DB_COLUMNS_DATA']['ORDER_DETAIL']['TASA_O_CUOTA'], String)

    def manage_orders_lines(self, tipo_pedido, order_id, order_item_guid, product_id, product_name, sku,
                            manufacturer_part_number, vendor_id, unit_price_incl_tax, unit_price_excltax,
                            price_incl_tax, price_excl_tax, quantity, discount_amount_incl_tax,
                            discount_amount_excl_tax, uom, line_number, inventory_item, inventory_item_id, tax_code,
                            item_comment, agreement_item, clave_prod_sat, clave_unidad_sat, clave_impuesto_sat,
                            tipo_factor_sat, tasaocuota_sat):

        order_line_data = {}

        try:
            session = self

            order_line_data = insert_new_order_line(session, tipo_pedido, order_id, order_item_guid, product_id,
                                                    product_name, sku, manufacturer_part_number, vendor_id,
                                                    unit_price_incl_tax, unit_price_excltax, price_incl_tax,
                                                    price_excl_tax, quantity, discount_amount_incl_tax,
                                                    discount_amount_excl_tax, uom, line_number, inventory_item,
                                                    inventory_item_id, tax_code, item_comment, agreement_item,
                                                    clave_prod_sat, clave_unidad_sat, clave_impuesto_sat,
                                                    tipo_factor_sat, tasaocuota_sat)

        except SQLAlchemyError as error:
            session.rollback()
            logger.exception('An exception was occurred while execute transactions: %s', error)
        finally:
            session.close()

        return order_line_data


def insert_new_order_line(session, tipo_pedido, order_id, order_item_guid, product_id, product_name, sku,
                          manufacturer_part_number, vendor_id, unit_price_incl_tax, unit_price_excltax,
                          price_incl_tax, price_excl_tax, quantity, discount_amount_incl_tax,
                          discount_amount_excl_tax, uom, line_number, inventory_item, inventory_item_id,
                          tax_code, item_comment, agreement_item, clave_prod_sat, clave_unidad_sat, clave_impuesto_sat,
                          tipo_factor_sat, tasaocuota_sat):
    order_line_inserted = []

    order_line_data = {}

    cfg = get_config_constant_file()

    table_name = cfg['DB_ORACLE_OBJECTS']['ORDER_L']

    last_update_date = get_systimestamp_date(session)
    user_id = cfg['DB_COL_DATA']['USER_ID']
    user_id_upd = cfg['DB_COL_DATA']['USER_ID']

    # Verifica que el insert de la linea por tu item_guid se haya realizado,
    # devolviendo un JSON verificador como response
    # row_exists = exists_data_row(session,
    #                              table_name,
    #                              'orderitemguid',
    #                              'orderid', order_id,
    #                              'tipo_pedido', tipo_pedido)

    row_exists = exists_data_row_item(session,
                                      table_name,
                                      'sku',
                                      'orderid', order_id,
                                      'tipo_pedido', tipo_pedido,
                                      'sku', sku)

    if str(order_item_guid) not in str(row_exists):

        new_order_line = OrderDetail(tipo_pedido=tipo_pedido,
                                     order_id=order_id,
                                     order_item_guid=order_item_guid,
                                     product_id=product_id,
                                     product_name=product_name,
                                     sku=sku,
                                     manufacturer_part_number=manufacturer_part_number,
                                     vendor_id=vendor_id,
                                     unit_price_incl_tax=unit_price_incl_tax,
                                     unit_price_excl_tax=unit_price_excltax,
                                     price_incl_tax=price_incl_tax,
                                     price_excl_tax=price_excl_tax,
                                     quantity=quantity,
                                     discount_amount_incl_tax=discount_amount_incl_tax,
                                     discount_amount_excl_tax=discount_amount_excl_tax,
                                     created_by=user_id,
                                     last_updated_by=user_id_upd,
                                     uom=uom,
                                     line_number=line_number,
                                     inventory_item=inventory_item,
                                     inventory_item_id=inventory_item_id,
                                     tax_code=tax_code, 
                                     item_comment=item_comment,
                                     agreement_item=agreement_item,
                                     clave_prod_serv_sat=clave_prod_sat,
                                     clave_unidad_sat=clave_unidad_sat,
                                     clave_impuesto_sat=clave_impuesto_sat,
                                     tipo_factor_sat=tipo_factor_sat,
                                     tasaocuota_sat=tasaocuota_sat)

        session.add(new_order_line)

        session.commit()

        order_line_inserted += [{
            "OrderId": order_id,
            "TipoPedido": tipo_pedido,
            "OrderItemGUID": order_item_guid,
            "Sku": sku,
            "Message": 'Item_Inserted'
        }]

    else:
        order_line_inserted += [{
            "OrderId": order_id,
            "TipoPedido": tipo_pedido,
            "OrderItemGUID": order_item_guid,
            "Sku": sku,
            "Message": 'Already_Inserted'
        }]

    order_line_data = json.dumps(order_line_inserted)

    return order_line_data


def update_status_order_item(session, table_name, order_id, order_type, item_status, sku_item):
    item_status_updated = []

    item_status_data = {}

    try:
        sql_status_item = " UPDATE {} " \
                          " SET status = {} " \
                          " WHERE orderid = {} " \
                          " AND tipo_pedido = {} " \
                          " AND sku = {}".format(table_name,
                                                 "'" + item_status + "'",
                                                 order_id,
                                                 "'" + order_type + "'",
                                                 "'" + sku_item + "'")

        status_item = session.execute(sql_status_item)

        if status_item is not None:

            row_exists = exists_data_row_item(session,
                                              table_name,
                                              'status',
                                              'orderid', order_id,
                                              'tipo_pedido', order_type,
                                              'sku', sku_item)

            if str(status_item) in str(row_exists):
                item_status_updated += [{
                    "OrderId": order_id,
                    "TipoPedido": order_type,
                    "StatusOK": 'OK',
                    "StatusItem": item_status,
                    "SKU": sku_item
                }]

        else:

            item_status_updated += [{
                "OrderId": order_id,
                "TipoPedido": order_type,
                "StatusOK": 'FAIL',
                "StatusItem": item_status,
                "SKU": sku_item
            }]

            logger.error('Can not read the recordset, beacause is not stored')
            raise SQLAlchemyError(
                "Can\'t read data because it\'s not stored in table {}. SQL Exception".format(table_name)
            )

        item_status_data = json.dumps(item_status_updated)

        session.commit()

        status_item.close()

    except SQLAlchemyError as sql_exec:
        logger.exception(sql_exec)
    finally:
        session.close()

    return item_status_data


def select_orders_header_cnc(session, table_name):
    # table_name = tv_orders_h

    order_headers = []

    data_orders_header = {}

    try:
        sql_head = " SELECT " \
                   "    orderid order_id," \
                   "    upper(vatnumber) rfc_cliente, " \
                   "    upper(billingfirstname) ||' '|| upper(BILLINGLASTNAME) nombre_cliente, " \
                   "    customer_number numero_cliente, " \
                   "    upper(BILLINGADDRESS1)||' '||upper(BILLINGADDRESS2) domicilio, " \
                   "    BILLINGENTRECALLES as domicilio_entrecalles, " \
                   "    BILLINGGNUMEROEXTERIOR as domicilio_numero_exterior, " \
                   "    upper(billingcity) ciudad, " \
                   "    upper(BILLINGSTATEPROVINCENAME) estado, " \
                   "    BILLINGZIPPOSTALCODE codigo_postal, " \
                   "    upper(BILLINGCOUNTRYNAME) pais, " \
                   "    BILLINGPHONENUMBER telefono_cliente, " \
                   "    BILLINGEMAIL correo_cliente, " \
                   "    '$ ' || (ordertotal - ordertax) || ' ' || customercurrencycode subtotal, " \
                   "    '$ ' || ordertax || ' ' || customercurrencycode impuesto_order, " \
                   "    '$ ' || ordertotal || ' ' || customercurrencycode total_order, " \
                   "    PAYMENTMETHODSYSTEMNAME forma_pago_order, " \
                   "    SHIPPINGMETHOD metodo_compra, " \
                   "    CREATEDONUTC fecha_order " \
                   " FROM {} " \
                   " WHERE status = 'PROCESO' " \
                   " AND PICKUPINSTORE = 'True' ".format(table_name)

        orders_header = session.execute(sql_head)

        for o_h in orders_header:
            if o_h is not None:

                print('Orders ClickNCollect: ', o_h)

                order_id = o_h['order_id']
                rfc_cliente = o_h['rfc_cliente']
                nombre_cliente = o_h['nombre_cliente']
                numero_cliente = o_h['numero_cliente']
                domicilio_cliente = o_h['domicilio']
                domicilio_entrecalles = o_h['domicilio_entrecalles']
                domicilio_numero_exterior = o_h['domicilio_numero_exterior']
                ciudad_cliente = o_h['ciudad']
                estado_cliente = o_h['estado']
                codigo_postal = o_h['codigo_postal']
                pais = o_h['pais']
                telefono_cliente = o_h['telefono_cliente']
                correo_cliente = o_h['correo_cliente']
                subtotal_pedido = o_h['subtotal']
                impuesto_pedido = o_h['impuesto_order']
                total_pedido = o_h['total_order']
                forma_pago_pedido = o_h['forma_pago_order']
                metodo_compra_pedido = o_h['metodo_compra']
                fecha_pedido = datetime.strptime(str(o_h['fecha_order']), "%Y-%m-%d %H:%M:%S")

                logger.info('Header Pedido: %s', 'OrderId: {}, '
                                                 'Nombre cliente: {}, '
                                                 'Domicilio: {}, '
                                                 'Telefono: {}, '
                                                 'Email: {}, '
                                                 'Importe pedido: {}, '
                                                 'Impuesto pedido: {}, '
                                                 'Total pedido: {},'
                                                 'Forma de pago: {}, '
                                                 'Metodo de pago: {}, '
                                                 'Fecha pedido: {}'.format(order_id,
                                                                           nombre_cliente,
                                                                           domicilio_cliente + ', ' + ciudad_cliente +
                                                                           ' ' + estado_cliente + ', ' +
                                                                           'C.P. ' + codigo_postal + ', ' + pais,
                                                                           telefono_cliente, correo_cliente,
                                                                           subtotal_pedido, impuesto_pedido,
                                                                           total_pedido, forma_pago_pedido,
                                                                           metodo_compra_pedido, fecha_pedido
                                                                           ))

                order_headers += [{
                    "OrderHeader": {
                        "OrderId": order_id,
                        "RfcCliente": rfc_cliente,
                        "NombreCliente": nombre_cliente,
                        "NumeroCliente": numero_cliente,
                        "Domicilio": domicilio_cliente,
                        "EntreCalles": domicilio_entrecalles,
                        "NumeroExterior": domicilio_numero_exterior,
                        "Ciudad": ciudad_cliente,
                        "Estado": estado_cliente,
                        "CodigoPostal": codigo_postal,
                        "Pais": pais,
                        "TelefonoCliente": telefono_cliente,
                        "EmailCliente": correo_cliente,
                        "ImportePedido": subtotal_pedido,
                        "ImpuestoPedido": impuesto_pedido,
                        "TotalPedido": total_pedido,
                        "FormaPago": forma_pago_pedido,
                        "MetodoPago": metodo_compra_pedido,
                        "FechaPedido": str(fecha_pedido)
                    }
                }]

            else:
                logger.error('Can not read the recordset, beacause is not stored')
                raise SQLAlchemyError(
                    "Can\'t read data because it\'s not stored in table {}. SQL Exception".format(table_name)
                )

        data_orders_header = json.dumps(order_headers)

        orders_header.close()

    except SQLAlchemyError as sql_exc:
        logger.exception(sql_exc)
    # finally:
    #    session.close()

    return data_orders_header


def select_orders_detail(session, order_id, order_type, table_name):
    # table_name = tv_orders_l

    order_detail_data = []

    data_order_detail = {}

    try:

        total_pedido = 0

        sql_detail = " SELECT tipo_pedido, orderid order_id, line_number, orderitemguid, productname nombre_producto," \
                     "        quantity cantidad_producto, sku, manufacturerpartnumber codigo_fabricante, " \
                     "        vendorid vendor_id, unitpriceincltax importe_total_producto, " \
                     "        unitpriceexcltax subtotal_producto, priceincltax total_item_order, " \
                     "        (unitpriceincltax - unitpriceexcltax) impuesto_producto," \
                     "        priceexcltax subtotal_item_order, uom unidad_medida, inventory_item_id, tax_code, " \
                     "        CLAVEPRODSERV clave_prod_sat, claveunidad clave_unidad_sat, " \
                     "        CLAVEIMPUESTO clave_impuesto_sat, tipofactor tipo_factor_sat, organization_id " \
                     " FROM {} " \
                     " WHERE orderid = {} " \
                     " AND tipo_pedido = {} " \
                     " ORDER BY orderid, line_number ASC".format(table_name, str(order_id), "'" + order_type + "'")

        orders_detail = session.execute(sql_detail)

        for o_l in orders_detail:
            if o_l is not None:

                tipo_pedido = o_l['tipo_pedido']
                order_id = o_l['order_id']
                line_number = o_l['line_number']
                order_item_guid = o_l['orderitemguid']
                nombre_producto = o_l['nombre_producto']
                cantidad_producto = o_l['cantidad_producto']
                sku = o_l['sku']
                codigo_fabricante = o_l['codigo_fabricante']
                vendor_id = o_l['vendor_id']
                importe_total_producto = str(o_l['importe_total_producto'])
                subtotal_producto = str(o_l['subtotal_producto'])
                importe_producto = str(o_l['impuesto_producto'])
                total_item_order = str(o_l['total_item_order'])
                subtotal_item_order = str(o_l['subtotal_item_order'])
                unidad_medida = o_l['unidad_medida']
                item_id = o_l['inventory_item_id']
                codigo_impuesto = o_l['tax_code']
                clave_prod_sat = o_l['clave_prod_sat']
                clave_unidad_sat = o_l['clave_unidad_sat']
                clave_impuesto_sat = o_l['clave_impuesto_sat']
                tipo_factor_sat = o_l['tipo_factor_sat']
                organization_id = o_l['organization_id']

                total_pedido += total_item_order

                logger.info('Cantidad Producto: {}, '
                            'SKU: {}, '
                            'Nombre Producto: {}, '
                            'Codigo Fabricante: {}, '
                            'Unidad medida: {}, '
                            'Importe partidas: {}, '
                            'Total partidas: {}, '
                            'Total: {}'.format(cantidad_producto, sku, nombre_producto, codigo_fabricante,
                                               unidad_medida,
                                               subtotal_item_order, total_item_order, total_pedido))

                order_detail_data += [{
                    "OrderDetail": {
                        "TipoPedido": tipo_pedido,
                        "OrderId": order_id,
                        "LineNumber": line_number,
                        "OorderItemGUId": order_item_guid,
                        "NombreProducto": nombre_producto,
                        "CantidadProducto": cantidad_producto,
                        "SKU": sku,
                        "CodigoFabricante": codigo_fabricante,
                        "VendorId": vendor_id,
                        "ImporteTotalProducto": str(importe_total_producto),
                        "SubtotalProducto": str(subtotal_producto),
                        "ImpuestoProducto": str(importe_producto),
                        "TotalItemOrder": str(total_item_order),
                        "SubtotalItemOrder": str(subtotal_item_order),
                        "UnidadMedida": unidad_medida,
                        "InventoryItemId": item_id,
                        "CodigoImpuesto": codigo_impuesto,
                        "ClaveProdSAT": clave_prod_sat,
                        "ClaveUnidadSAT": clave_unidad_sat,
                        "ClaveImpuestoSAT": clave_impuesto_sat,
                        "TipoFactorSAT": tipo_factor_sat,
                        "OrganizationId": organization_id
                    }
                }]

            else:
                logger.error('Can not read the recordset, beacause is not stored')
                raise SQLAlchemyError(
                    "Can\'t read data because it\'s not stored in table {}. SQL Exception".format(table_name)
                )

        data_order_detail = json.dumps(order_detail_data)

        orders_detail.close()

    except SQLAlchemyError as sql_exc:
        logger.exception(sql_exc)
    finally:
        session.close()

    return data_order_detail


def select_status_order_by_id(session, table_name, order_id, tipo_pedido):
    order_status = []

    order_status_data = {}

    try:
        sql_status_order = " SELECT status" \
                           " FROM {} " \
                           " WHERE tipo_pedido = {} " \
                           " AND orderid = {} ".format(table_name, "'" + tipo_pedido + "'", order_id)

        status_order = session.execute(sql_status_order)

        order_status = [{
            "OrderId": order_id,
            "StatusPedido": "SIN ESTATUS",
            "TipoPedido": tipo_pedido
        }]

        for o_s in status_order:
            if o_s is not None:

                status_pedido = o_s['status']

                order_status = [{
                    "OrderId": order_id,
                    "StatusPedido": status_pedido,
                    "TipoPedido": tipo_pedido
                }]

            else:

                order_status = [{
                    "OrderId": order_id,
                    "StatusPedido": "SIN ESTATUS",
                    "TipoPedido": tipo_pedido
                }]

                logger.error('Can not read the recordset, beacause is not stored')
                raise SQLAlchemyError(
                    "Can\'t read data because it\'s not stored in table {}. SQL Exception".format(table_name)
                )

        order_status_data = json.dumps(order_status)

        status_order.close()

    except SQLAlchemyError as sql_exec:
        order_status = [{
            "OrderId": order_id,
            "StatusPedido": "SIN ESTATUS",
            "TipoPedido": tipo_pedido
        }]
        logger.exception(sql_exec)
    finally:
        session.close()

    return order_status_data


def update_status_order_by_id(session, table_name, order_id, order_type, order_status):
    order_status_updated = []

    order_status_data = {}

    try:
        sql_status_order = " UPDATE {} " \
                           " SET status = {} " \
                           " WHERE orderid = {} " \
                           " AND   tipo_pedido = {} ".format(table_name,
                                                             "'" + order_status + "'",
                                                             order_id,
                                                             "'" + order_type + "'")

        status_order = session.execute(sql_status_order)

        if status_order is not None:

            row_exists = exists_data_row(session,
                                         table_name,
                                         'status',
                                         'orderid', order_id,
                                         'tipo_pedido', order_type)

            if str(order_status) in str(row_exists):
                order_status_updated += [{
                    "OrderId": order_id,
                    "StatusOK": 'OK',
                    "TipoPedido": order_type
                }]

        else:

            order_status_updated += [{
                "OrderId": order_id,
                "StatusOK": 'FAIL',
                "TipoPedido": order_type
            }]

            logger.error('Can not read the recordset, beacause is not stored')
            raise SQLAlchemyError(
                "Can\'t read data because it\'s not stored in table {}. SQL Exception".format(table_name)
            )

        order_status_data = json.dumps(order_status_updated)

        session.commit()

        status_order.close()

    except SQLAlchemyError as sql_exec:
        logger.exception(sql_exec)
    finally:
        session.close()

    return order_status_data


def select_integracion_id_by_vendor_id(session, vendor_id):
    cfg = get_config_constant_file()

    __tablename__ = cfg['DB_ORACLE_OBJECTS']['TV_INTEGRACIONES_OFIX']

    # columns names

    integracion_id = cfg['DB_COLUMNS_DATA']['TV_INTEGRACIONES']['INTEGRACION_ID']
    integracion_name = cfg['DB_COLUMNS_DATA']['TV_INTEGRACIONES']['INTEGRACION_NAME']
    status = cfg['DB_COLUMNS_DATA']['TV_INTEGRACIONES']['STATUS']
    vendorid = cfg['DB_COLUMNS_DATA']['TV_INTEGRACIONES']['VENDOR_ID']
    tienda_virtual_id = cfg['DB_COLUMNS_DATA']['TV_INTEGRACIONES']['TIENDA_VIRTUAL_ID']
    inventario_minimo = cfg['DB_COLUMNS_DATA']['TV_INTEGRACIONES']['INVENTARIO_MINIMO']
    precio_minimo_venta = cfg['DB_COLUMNS_DATA']['TV_INTEGRACIONES']['PRECIO_MINIMO_VENTA']

    integracion_data = []

    integraciones = {}

    try:
        sql_integracion_data = " SELECT " \
                               "     {}, " \
                               "     {} AS integracion_name, " \
                               "     {}, " \
                               "     {}, " \
                               "     {}, " \
                               "     {}, " \
                               "     {} " \
                               " FROM {} " \
                               " WHERE {} = {} " \
                               "AND status = 'ACTIVO'".format(integracion_id,
                                                              integracion_name,
                                                              status,
                                                              vendorid,
                                                              tienda_virtual_id,
                                                              inventario_minimo,
                                                              precio_minimo_venta,
                                                              __tablename__,
                                                              vendorid,
                                                              vendor_id)

        integracion_db = session.execute(sql_integracion_data)

        integracion_data = [{
            "IntegracionId": -1,
            "IntegracionName": "null",
            "StatusIntegracion": "null",
            "VendorId": vendor_id,
            "TiendaVirtualId": "0",
            "InventarioMinimo": 0,
            "PrecioMinimoVenta": 0
        }]

        for integracion in integracion_db:
            if integracion is not None:

                r_integracion_id = integracion['integracion_id']
                r_integracion_name = integracion['integracion_name']
                r_status_integracion = integracion['status']
                r_vendor_id = integracion['vendorid']
                r_tienda_virtual_id = integracion['tienda_virtual_id']
                r_inventario_minimo = integracion['inventario_minimo']
                r_precio_minimo_venta = integracion['precio_minimo_venta']

                integracion_data = [{
                    "IntegracionId": r_integracion_id,
                    "IntegracionName": r_integracion_name,
                    "StatusIntegracion": r_status_integracion,
                    "VendorId": r_vendor_id,
                    "TiendaVirtualId": r_tienda_virtual_id,
                    "InventarioMinimo": r_inventario_minimo,
                    "PrecioMinimoVenta": r_precio_minimo_venta
                }]

            else:
                logger.error('Can not read the recordset, beacause is not stored')
                raise SQLAlchemyError(
                    "Can\'t read data because it\'s not stored in table {}. SQL Exception".format(__tablename__)
                )

        integraciones = json.dumps(integracion_data)

        integracion_db.close()

    except SQLAlchemyError as sql_exec:
        logger.exception(sql_exec)
    finally:
        session.close()

    return integraciones


def validate_user_exists(user_name):
    cfg = get_config_constant_file()

    conn = session_to_db()

    cursor = conn.cursor()

    table_name = cfg['DB_AUTH_OBJECT']['USERS_AUTH']

    sql_check = "SELECT EXISTS(SELECT 1 FROM {} WHERE user_name = {} LIMIT 1)".format(table_name, "'" + user_name + "'")

    cursor.execute(sql_check)

    result = cursor.fetchone()

    return result


def update_user_password_hashed(user_name, password_hash):
    cfg = get_config_constant_file()

    conn = session_to_db()

    cursor = conn.cursor()

    last_update_date = get_datenow_from_db(conn)

    table_name = cfg['DB_AUTH_OBJECT']['USERS_AUTH']

    # update row to database
    sql_update_user = "UPDATE {} SET password_hash = %s, last_update_date = NOW() WHERE user_name = %s".format(
        table_name
    )

    cursor.execute(sql_update_user, (password_hash, user_name,))

    conn.commit()

    close_cursor_postgre(cursor)


def insert_user_authenticated(user_id, user_name, user_password, password_hash):
    cfg = get_config_constant_file()

    conn = session_to_db()

    cursor = conn.cursor()

    last_update_date = get_datenow_from_db(conn)

    table_name = cfg['DB_AUTH_OBJECT']['USERS_AUTH']

    data = (user_id, user_name, user_password, password_hash,)

    sql_user_insert = 'INSERT INTO {} (user_id, user_name, user_password, password_hash) ' \
                      'VALUES (%s, %s, %s, %s)'.format(table_name)

    cursor.execute(sql_user_insert, data)

    conn.commit()

    logger.info('Usuario insertado %s', "{0}, User_Name: {1}".format(user_id, user_name))

    close_cursor_postgre(cursor)


class UsersAuth(Base):
    cfg = get_config_constant_file()

    __tablename__ = cfg['DB_AUTH_OBJECT']['USERS_AUTH']

    user_id = Column(cfg['DB_AUTH_COLUMNS_DATA']['USERS_ORDERS']['USER_ID'], Numeric, primary_key=True)
    user_name = Column(cfg['DB_AUTH_COLUMNS_DATA']['USERS_ORDERS']['USER_NAME'], String, primary_key=True)
    user_password = Column(cfg['DB_AUTH_COLUMNS_DATA']['USERS_ORDERS']['USER_PASSWORD'], String)
    password_hash = Column(cfg['DB_AUTH_COLUMNS_DATA']['USERS_ORDERS']['PASSWORD_HASH'], String)
    last_update_date = Column(cfg['DB_AUTH_COLUMNS_DATA']['USERS_ORDERS']['LAST_UPDATE_DATE'], String)

    @staticmethod
    def manage_user_authentication(self, user_name, user_password, password_hash):

        user_id = 0

        try:

            user_id += 1

            user_verification = validate_user_exists(user_name)

            # insert validation
            if user_verification[0]:

                # update method
                update_user_password_hashed(user_name, password_hash)

            else:
                # insert

                user_id += 1

                insert_user_authenticated(user_id, user_name, user_password, password_hash)

        except SQLAlchemyError as e:
            logger.exception('An exception was occurred while execute transactions: %s', e)
            raise mvc_exc.ItemNotStored(
                'Can\'t insert user_id: "{}" with user_name: {} because it\'s not stored in "{}"'.format(
                    user_id, user_name, UsersAuth.__tablename__
                )
            )


def get_data_user_authentication(session, table_name, user_name):
    user_auth = []

    user_auth_data = {}

    try:
        sql_user_data = " SELECT user_name, user_password, password_hash, last_update_date " \
                        " FROM {} " \
                        " WHERE user_name = {} ".format(table_name, "'" + user_name + "'")

        user_auth_db = session.execute(sql_user_data)

        for user in user_auth_db:
            if user is not None:

                user_name_db = user['username']
                user_password_db = user['password']
                password_hash = user['password_hash']
                last_update_date = datetime.strptime(str(user['last_update_date']), "%Y-%m-%d")

                user_auth += [{
                    "username": user_name_db,
                    "password": user_password_db,
                    "password_hash": password_hash,
                    "date_updated": last_update_date
                }]

            else:
                logger.error('Can not read the recordset, beacause is not stored')
                raise SQLAlchemyError(
                    "Can\'t read data because it\'s not stored in table {}. SQL Exception".format(table_name)
                )

        user_auth_data = json.dumps(user_auth)

        user_auth_db.close()

    except SQLAlchemyError as sql_exec:
        logger.exception(sql_exec)
    finally:
        session.close()

    return user_auth_data


# Define y obtiene el configurador para las constantes del sistema:
def get_config_constant_file():
    """
        Contiene la obtencion del objeto config
        para setear datos de constantes en archivo
        configurador

    :rtype: object
    """

    # PROD
    # _constants_file = "/var/www/html/apiTestOrdersTV/constants/constants.yml"

    # TEST
    _constants_file = "constants/constants.yml"

    cfg = Const.get_constants_file(_constants_file)

    return cfg