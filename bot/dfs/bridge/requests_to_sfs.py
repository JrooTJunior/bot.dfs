# -*- coding: utf-8 -*-
import json
from zeep import Client, helpers


class RequestsToSfs(object):
    def __init__(self):
        super(RequestsToSfs, self).__init__()
        self.sfs_client = Client('http://obmen.sfs.gov.ua/SwinEd.asmx?WSDL')

    def sfs_check_request(self, edr_id):
        sfs_check = self.sfs_client.service.Check(recipientEDRPOU=edr_id)
        sfs_check_to_dict = soap_to_dict(sfs_check)
        return sfs_check_to_dict

    def sfs_receive_request(self, edr_id, ca_name, cert):
        sfs_receive = self.sfs_client.service.Receive(recipientEDRPOU=edr_id, caName=ca_name, cert=cert)
        sfs_receive_to_dict = soap_to_dict(sfs_receive)
        return sfs_receive_to_dict


def soap_to_dict(soap_object):
    return json.loads(json.dumps(helpers.serialize_object(soap_object)))
