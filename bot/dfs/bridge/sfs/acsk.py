# coding=utf-8
import json
import logging
import os
import requests

VERIFY_SSL = False  # Disabled SSL verification due to invalid local ca-bundle.

log = logging.getLogger('acsk')


class Acsk:
    def __init__(self, acsk, acsk_id, certificates_dir):
        self.acsk = acsk
        self.acsk_id = acsk_id
        self.certificates_dir = certificates_dir
        self.cas = {}
        self.StoreSettings = {"szPath": '',
                              "bCheckCRLs": True,
                              "bAutoRefresh": True,
                              "bOwnCRLsOnly": False,
                              "bFullAndDeltaCRLs": False,
                              "bAutoDownloadCRLs": True,
                              "bSaveLoadedCerts": True,
                              "dwExpireTime": 3600}
        self.ProxySettings = {"bUseProxy": False,
                              "bAnonymous": False,
                              "szAddress": "",
                              "szPort": "",
                              "szUser": "",
                              "szPassword": "",
                              "bSavePassword": False}
        self.OCSPSettings = {"bUseOCSP": False,
                             "bBeforeStore": False,
                             "szAddress": '',
                             "szPort": ''}
        self.TSPSettings = {"bGetStamps": False,
                            "szAddress": '',
                            "szPort": ''}
        self.CMPSettings = {"bUseCMP": False,
                            "szAddress": '',
                            "szPort": '',
                            "szCommonName": ''}
        self.LDAPSettings = {"bUseLDAP": False,
                             "szAddress": "",
                             "szPort": "",
                             "bAnonymous": False,
                             "szUser": "",
                             "szPassword": ""}
        self.ModeSettings = {"bOfflineMode": True}

    @classmethod
    def load(cls, acsk_id, certificates_dir):
        # type: (int, str) -> Acsk
        cas = CAsLoader(acsk_id).get()
        return cls(cas, acsk_id, certificates_dir)

    def set_storage_settings(self, euscp, path):
        self.StoreSettings["szPath"] = path
        if not os.path.isdir(self.StoreSettings.get('szPath')):
            os.makedirs(self.StoreSettings.get('szPath'))
        euscp.SetFileStoreSettings(self.StoreSettings)
        dS = {}
        euscp.GetFileStoreSettings(dS)
        if len(dS["szPath"]) != 0:
            euscp.SetProxySettings(self.ProxySettings)
            euscp.SetProxySettings(self.ProxySettings)
            return True
        else:
            return False

    def set_OCSP(self, euscp, csk):
        self.cas = self.acsk[csk]
        if len(self.cas.get('ocspAccessPointAddress')) > 0:
            self.OCSPSettings["bUseOCSP"] = True
            self.OCSPSettings["bBeforeStore"] = True
            self.OCSPSettings["szAddress"] = self.cas.get('ocspAccessPointAddress')
            self.OCSPSettings["szPort"] = self.cas.get('ocspAccessPointPort')
            self.ModeSettings["bOfflineMode"] = False
        euscp.SetOCSPSettings(self.OCSPSettings)

    def set_TSP(self, euscp, csk):
        self.cas = self.acsk[csk]
        if len(self.cas.get('tspAddress')) > 0:
            self.TSPSettings["bGetStamps"] = True
            self.TSPSettings["szAddress"] = self.cas.get('tspAddress')
            self.TSPSettings["szPort"] = self.cas.get('tspAddressPort')
        euscp.SetLDAPSettings(self.LDAPSettings)

    def set_CMP(self, euscp, csk):
        self.cas = self.acsk[csk]
        if len(self.cas.get("cmpAddress")) > 0:
            self.CMPSettings["bUseCMP"] = True
            self.CMPSettings["szAddress"] = self.cas.get("cmpAddress")
            self.CMPSettings["szPort"] = '80'
            self.CMPSettings["szCommonName"] = ''
            self.ModeSettings["bOfflineMode"] = False
        euscp.SetCMPSettings(self.CMPSettings)

    def set_mode_settings(self, euscp):
        euscp.SetModeSettings(self.ModeSettings)

    def configure(self, euscp):
        if not self.set_storage_settings(euscp, self.certificates_dir):
            log.error('Failed to load certificates!')
            return False

        self.set_OCSP(euscp, self.acsk_id)
        self.set_TSP(euscp, self.acsk_id)
        self.set_CMP(euscp, self.acsk_id)
        self.set_mode_settings(euscp)

        return True


class CAsLoader(object):
    def __init__(self, acsk, path=None):
        if path is None:
            path = ''
        self.path = path
        self.cas_file = os.path.join(path, '.CAs.json')
        self.acsk = acsk

    @staticmethod
    def check_host(host):
        try:
            sc = requests.head(host, verify=VERIFY_SSL).status_code
            log.debug('host {} response code {}'.format(host, sc))
            if 200 >= sc <= 299:
                return True
            else:
                log.error('host {} response code {}'.format(host, sc))
                return False
        except Exception as err:
            log.critical('Exception: {}'.format(err))
            return False

    def get(self):
        if not all(map(self.check_host, ['https://czo.gov.ua', 'https://iit.com.ua/download/productfiles/CAs.json'])):
            log.error('Failed to load CAs')
        if os.path.isfile(self.cas_file):
            with open(self.cas_file, 'r') as f:
                CAS = json.load(f)
        else:
            CAS = requests.get('https://iit.com.ua/download/productfiles/CAs.json', verify=VERIFY_SSL).json()
            with open(self.cas_file, 'w') as f:
                json.dump(CAS, f)
        if not self.check_host('https://' + CAS[self.acsk].get('address')):
            log.error('Failed to load CAs')
            raise RuntimeError('Failed to load CAs!')
        return CAS
