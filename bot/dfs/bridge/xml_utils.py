# coding=utf-8
import datetime

import logging
import os
import pytz as pytz
import xmlschema
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring, fromstring

from sfs.filename import Filename

logger = logging.getLogger(__name__)


def is_valid(request):
    schema = xmlschema.XMLSchema(os.path.join(os.getcwd(), "resources/J1603101.xsd"))
    return schema.is_valid(request)


def form_xml_to_post(data, request_id):
    request = Element('request')
    hnum = SubElement(request, "HNUM")
    hnum.text = str(request_id)
    htin = SubElement(request, "HTIN")
    htin.text = u'02426097'
    hfill = SubElement(request, "HFILL")
    hfill.text = str(datetime.date.today())
    htime = SubElement(request, "HTIME")
    htime.text = str(datetime.datetime.now().time().replace(microsecond=0))
    hname = SubElement(request, "HNAME")
    hname.text = u'ДП «ПРОЗОРРО»'
    hksti = SubElement(request, "HKSTI")
    hksti.text = str(2659)
    hsti = SubElement(request, "HSTI")
    hsti.text = u'ДПI у Шевченківському районі ГУ ДФС у м.Києві'
    r0101g1s = SubElement(request, "R0101G1S")
    r0101g1s.text = data.tender_id
    r0201g1s = SubElement(request, "R0201G1S")
    r0201g1s.text = data.code
    r0202g1s = SubElement(request, "R0202G1S")
    if r0201g1s.text == data.code:
        r0202g1s.text = data.name
    r0203g1s = SubElement(request, "R0203G1S")
    r0204g1s = SubElement(request, "R0204G1S")
    r0205g1s = SubElement(request, "R0205G1S")
    if data.is_physical:
        r0203g1s.text = data.first_name
        r0204g1s.text = data.last_name
        r0205g1s.text = data.family_name

    logger.info("Request {} is valid? {}".format(request_id, is_valid(request)))


def form_yaml_from_response():
    return {"data": "placeholder"}


def get_now():
    return datetime.datetime.now(pytz.timezone('Europe/Kiev'))


def element_with_text(root, tag, text, attrs=None):
    el = SubElement(root, tag, attrs or {})
    if not isinstance(text, (str, unicode)):
        text = str(text)
    el.text = text
    return el


ORG = '2659'
C_DOC = 'J16'
C_DOC_SUB = 31
C_DOC_VER = 1
C_DOC_TYPE = 0
C_REG = 24
C_RAJ = 12
PERIOD_TYPE = 1
C_DOC_STAN = 1
SOFTWARE = 'ProZorro SFS integration Bot [test]'


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = tostring(elem, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ", encoding='utf-8')


from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader('resources', encoding='windows-1251'),
)
env.globals['str'] = str


def generate_request(data, request_id):
    # TODO: Change to real

    now = get_now()

    filename = Filename(org=ORG,
                        sender_erdpou='1010101017',
                        c_doc=C_DOC,
                        c_doc_sub=C_DOC_SUB,
                        c_doc_ver=C_DOC_VER,
                        c_doc_stan=C_DOC_STAN,
                        c_doc_type=C_DOC_TYPE,
                        c_doc_cnt=request_id,
                        period_type=PERIOD_TYPE,
                        period_month=now.month,
                        period_year=now.year,
                        file_ext='.XML')

    template = env.get_template('request.xml')
    content = template.render({'data': data, 'now': now, 'doc_num': request_id, 'request_id': 42}).encode('utf-8')

    # print '::', filename.export()
    # print '::', content

    request = fromstring(content)
    if not is_valid(request):
        raise ValueError('Generated request for {code} is invalid!'.format(code=data.code))
    return content, filename.export()
