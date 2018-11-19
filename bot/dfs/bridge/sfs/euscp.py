# coding=utf-8
import base64
import contextlib
import logging
import os
import struct

from .EUSignCP.Usage.v2.Interface.x64.EUSignCP import *
from .acsk import Acsk

VERIFY_SSL = False  # Disabled SSL verification due to invalid local ca-bundle.
acsk_log = logging.getLogger('acsk')
net_log = logging.getLogger('net')
euscp_log = logging.getLogger('euscp')


class EUSignCP(object):
    def __init__(self, key, password, certificate_name, certificates_dir):
        self.key = key
        self.password = password
        self.certificates_dir = certificates_dir
        self.certificate_name = certificate_name

        self.certificate = os.path.join(certificates_dir, certificate_name)
        self.lData = self._load_lData()
        self.acsk = Acsk.load(0, certificates_dir)
        self.keys = [[0, key, password, self.certificate]]  # Allow to use keys-chain

    def _load_lData(self):
        with open(os.path.join(self.certificates_dir, 'SFS2.cer')) as f:
            return [f.read()]

    def _load_lib(self):
        try:
            EULoad()
        except RuntimeError:
            euscp_log.error('Failed to load EUSignCP library.')
            raise

        pIface = EUGetInterface()
        pIface.Initialize()
        euscp_log.info('EUSignCP initialized.')

        if not self.acsk.configure(pIface):
            pIface.Finalize()
            EUUnload()
            raise RuntimeError('Failed to configure EUSignCP')

        return pIface

    def _unload_lib(self, pIface):
        pIface.Finalize()
        EUUnload()
        euscp_log.info('EUSignCP library unloaded.')

    @contextlib.contextmanager
    def open_pIface(self):
        euscp = self._load_lib()
        yield euscp
        self._unload_lib(euscp)

    @staticmethod
    def _sign(bblock, bdata):
        return bblock + struct.pack('<i', len(bdata)) + bdata

    def to_sfs(self, pData):
        with self.open_pIface() as pIface:
            try:
                lSign = None

                # Read keys
                for index, kkey in enumerate(self.keys, start=1):
                    try:
                        pIface.ReadPrivateKeyFile(kkey[1], kkey[2], None)
                    except RuntimeError, e:
                        euscp_log.error('Failed to read key {}: {}'.format(index, e))
                        raise

                    euscp_log.info('Read {} key.'.format(index))

                    # Impose sign
                    lSign = []
                    pIface.SignDataInternal(True, pData, len(pData), None, lSign)
                    euscp_log.info('EDS {} imposed'.format(index))
                    if index != len(self.keys):
                        pData = self._sign(b"UA1_SIGN\0", lSign[0])
                        euscp_log.info('Unload key {index}')
                        pIface.ResetPrivateKey()
                    else:
                        lSign[0] = self._sign(b"UA1_SIGN\0", lSign[0])

                # Read certificate "Протокол расподілу ключів"
                with open(self.keys[0][3], 'rb') as f:
                    euscp_log.info('Read certificate')
                    bCert = self._sign(b"CERTCRYPT\0", f.read())

                # Encryption
                lBdata = []
                pIface.EnvelopDataToRecipientsWithDynamicKey(dwRecipientCerts=self.lData,
                                                             bSignData=False,
                                                             bAppendCert=False,
                                                             pbData=lSign[0],
                                                             dwDataLength=len(lSign[0]),
                                                             ppszEnvelopedData=None,
                                                             ppbEnvelopedData=lBdata)

                lBdata[0] = self._sign(b"UA1_CRYPT\0", lBdata[0])
                euscp_log.info('Data encrypted.')

                bData = bCert + lBdata[0]

                lSignEnd = []
                pIface.SignDataInternal(True, bData, len(bData), None, lSignEnd)

                lBdata = self._sign(b"UA1_SIGN\0", lSignEnd[0])
                euscp_log.info('EDS imposed')
            except RuntimeError:
                euscp_log.exception('Failed to impose signs.')
                raise
            else:
                return lBdata

    def from_sfs(self, bData):
        with self.open_pIface() as pIface:
            try:
                # Читаю ключ
                cOInfo = {}
                pIface.ReadPrivateKeyFile(self.keys[-1][1], self.keys[-1][2], cOInfo)
                euscp_log.info('Key read')

                if bData[:10] == b'UA1_CRYPT\0':
                    pData = []
                    pIface.DevelopData(pszEnvelopedData=None,
                                       pbEnvelopedData=bData[14:],
                                       dwEnvelopedDataLength=len(bData[14:]),
                                       ppbData=pData,
                                       pInfo=None)
                    euscp_log.info('Encrypted data')

                    if pData[0][:9] == b'UA1_SIGN\0':
                        Data = []
                        pIface.VerifyDataInternal(pszSignedData=None,
                                                  pbSignedData=pData[0][13:],
                                                  dwSignedDataLength=len(pData[0][13:]),
                                                  ppbData=Data,
                                                  pSignInfo=None)
                        euscp_log.info('Encrypted sign')
                        lBdata = Data[0]

            except Exception as err:
                euscp_log.error(err)
                pIface.Finalize()
                EUUnload()
                raise err
            else:
                euscp_log.info('Finished!')
                return lBdata

    def encode(self, data):
        """
        Convert to Base64

        :param data: str
        :return: str
        """
        return base64.standard_b64encode(data).decode()

    def decode(self, data):
        """
        Decode Base64 string

        :param data: str
        :return: str
        """
        return base64.b64decode(data)

    def encrypt(self, data):
        """
        Prepare data for sending to SFS

        :param data: str
        :return: str
        """
        return self.encode(self.to_sfs(data))

    def decrypt(self, data):
        """
        Read data from SFS

        :param data: str
        :return: str
        """
        return self.from_sfs(self.decode(data))
