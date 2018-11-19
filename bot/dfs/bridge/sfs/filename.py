ORG = "2659"
PROZORRO_EDRPOU = "0002426097"
C_DOC = "J16"
C_DOC_SUB = "031"
C_DOC_VER = 1
C_DOC_STAN = 1
C_DOC_TYPE = 0
C_DOC_CNT = 1
PERIOD_TYPE = 1
PERIOD_MONTH = 1
PERIOD_YEAR = 1970

FILE_EXT = '.XML'


class Filename(object):
    def __init__(self,
                 org=ORG,
                 sender_erdpou=PROZORRO_EDRPOU,
                 c_doc=C_DOC,
                 c_doc_sub=C_DOC_SUB,
                 c_doc_ver=C_DOC_VER,
                 c_doc_stan=C_DOC_STAN,
                 c_doc_type=C_DOC_TYPE,
                 c_doc_cnt=C_DOC_CNT,
                 period_type=PERIOD_TYPE,
                 period_month=PERIOD_MONTH,
                 period_year=PERIOD_YEAR,
                 file_ext=FILE_EXT):
        self.org = org  # type: str
        self.sender_edrpou = sender_erdpou  # type: str
        self.c_doc = c_doc  # type: str
        self.c_doc_sub = c_doc_sub  # type: str
        self.c_doc_ver = c_doc_ver  # type: int
        self.c_doc_stan = c_doc_stan  # type: int
        self.c_doc_type = c_doc_type  # type: int
        self.c_doc_cnt = int(c_doc_cnt)  # type: int
        self.period_type = period_type  # type: int
        self.period_month = int(period_month)  # type: int
        self.period_year = int(period_year)  # type: int
        self.file_ext = file_ext  # type: int

    def export(self):
        return "{org:}" \
               "{sender_edrpou}" \
               "{c_doc}{c_doc_sub}{c_doc_ver}" \
               "{c_doc_stan}" \
               "{c_doc_type}" \
               "{c_doc_cnt}" \
               "{period_type}" \
               "{period_month}" \
               "{period_year}" \
               "{org:}" \
               "{file_ext}".format(org=str(self.org).rjust(4, '0'),
                                   sender_edrpou=str(self.sender_edrpou).rjust(10, '0'),
                                   c_doc=str(self.c_doc),
                                   c_doc_sub=str(self.c_doc_sub).rjust(3),
                                   c_doc_ver=str(self.c_doc_ver).rjust(2, '0'),
                                   c_doc_stan=str(self.c_doc_stan),
                                   c_doc_type=str(self.c_doc_type).rjust(2, '0'),
                                   c_doc_cnt=str(self.c_doc_cnt).rjust(7, '0'),
                                   period_type=str(self.period_type),
                                   period_month=str(self.period_month).rjust(2, '0'),
                                   period_year=str(self.period_year),
                                   file_ext=str(self.file_ext),
                                   )

    @classmethod
    def read(cls, string):
        if len(string) != 47 or string[-4] != '.' or string[:4] != string[39:43]:
            raise ValueError('Invalid filename!')
        org = string[:4]
        sender_erdpou = string[5:14]
        c_doc = string[14:17]
        c_doc_sub = string[17:20]
        c_doc_ver = string[20:22]
        c_doc_stan = string[22]
        c_doc_type = string[23:25]
        c_doc_cnt = int(string[25:32])
        period_type = string[32]
        period_month = int(string[33:35])
        period_year = int(string[35:39])
        file_ext = string[-4:]

        return cls(
            org=org,
            sender_erdpou=sender_erdpou,
            c_doc=c_doc,
            c_doc_sub=c_doc_sub,
            c_doc_ver=c_doc_ver,
            c_doc_stan=c_doc_stan,
            c_doc_type=c_doc_type,
            c_doc_cnt=c_doc_cnt,
            period_type=period_type,
            period_month=period_month,
            period_year=period_year,
            file_ext=file_ext,
        )

    def __str__(self):
        return self.export()

    def __repr__(self):
        return str(self)
