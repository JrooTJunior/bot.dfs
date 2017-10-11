# -*- coding: utf-8 -*-
from zeep import Client


class RequestsToSfs(object):
    def __init__(self):
        super(RequestsToSfs, self).__init__()
        self.sfs_client = Client('http://obmen.sfs.gov.ua/SwinEd.asmx?WSDL')

    def sfs_check_request(self, edr_code):
        sfs_check = self.sfs_client.service.Check(recipientEDRPOU=edr_code, recipientDept=1, procAllDepts=1)
        qtDocs = sfs_check.qtDocs
        return qtDocs

    def sfs_receive_request(self, edr_code, ca_name, cert):
        sfs_receive = self.sfs_client.service.Receive(recipientEDRPOU=edr_code, recipientDept=1, procAllDepts=1,
                                                      caName=ca_name, cert=cert)
        docs = sfs_receive.docs
        return docs

    def sfs_get_certificate_request(self, ca_name):
        sfs_get_certificate = self.sfs_client.service.GetCertificate(caName=ca_name)
        cert = sfs_get_certificate.certs.Certificate[0].cert
        return cert
