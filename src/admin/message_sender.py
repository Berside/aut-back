import logging
import logging.handlers

from ldap3 import Server, Connection, Tls, NTLM
import ssl
from src.configuration import configuration


tls_config = Tls(
    validate=ssl.CERT_REQUIRED,
    ca_certs_file='/etc/pki/tls/certs/ca-bundle.crt',
    version=ssl.PROTOCOL_TLSv1_2
)


def send_log(message, sender):
    if configuration['AUTH_DEBUG_MODE']:
        return 0
    try:
        logger = logging.getLogger("admin")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.handlers.SysLogHandler(
                address=(configuration['LDAP_SERVER_IP'], 514)
            )
            logger.addHandler(handler)

        logger.info(f"[{sender}] {message}")
    except:
        print("Send log error")
        print(sender, message)

def send_Permission_rule(attr):
    if configuration['AUTH_DEBUG_MODE']:
        return 0
    try:
        server = Server(
            configuration['LDAP_SERVER'],
            port=configuration['LDAP_PORT'],
            use_ssl=True,
            tls=tls_config,
            get_info=all
        )

        conn = Connection(
            server,
            user=configuration['LDAP_USER'],
            password=configuration['LDAP_USER_PASSWORD'],
            auto_bind=True,
            authentication=NTLM,
        )

        
        dn = (
            f"CN={attr['name']},"
            f"OU={configuration['OU']},"
            f"{configuration['LDAP_SEARCH_BASE']}"
        )

        result = conn.add(
            dn,
            object_class=["top", "SecurityRule"],
            attributes={
                "cn": attr['name'],
                "securityRuleType": "access_rule",
                "securityAdGroups": attr['ad_groups'],
                "securityRuleData":attr['code']
                }
        )

        print(result)
        print(conn.result)

        conn.unbind()
    except:
        print("Send Permission rule error")


def get_security_rules():
    if configuration['AUTH_DEBUG_MODE']:
        return 0
    try:
        server = Server(
            configuration['LDAP_SERVER'],
            port=configuration['LDAP_PORT'],
            use_ssl=True,
            tls=tls_config,
            get_info=all
        )

        conn = Connection(
            server,
            user=configuration['LDAP_USER'],
            password=configuration['LDAP_USER_PASSWORD'],
            auto_bind=True,
            authentication=NTLM,
        )


        conn.search(
            search_base=configuration['LDAP_SEARCH_BASE'],
            search_filter="(objectClass=SecurityRule)",
            search_scope="SUBTREE",
            attributes=[
                "cn",
                "securityRuleType",
                "securityAdGroups",
                "securityRuleData",
                "securityRuleEnabled",
                "description"
            ]
        )

        print( [entry.entry_attributes_as_dict for entry in conn.entries])

        conn.unbind()
    except:
        print('Get security rules error')


def get_ad_groups_from_server():
    if configuration['AUTH_DEBUG_MODE']:
        return 0
    try:
        server = Server(
            configuration['LDAP_SERVER'],
            port=configuration['LDAP_PORT'],
            use_ssl=True,
            tls=tls_config,
            get_info=all
        )

        conn = Connection(
            server,
            user=configuration['LDAP_USER'],
            password=configuration['LDAP_USER_PASSWORD'],
            auto_bind=True,
            authentication=NTLM,
        )
    
        conn.search(
            search_base="DC=server,DC=local",
            search_filter="(&(objectCategory=group)(objectClass=group))",
            attributes=[
                "cn",
                "sAMAccountName",
                "distinguishedName",
                "description",
                "member"
            ]
        )

        groups = []

        for entry in conn.entries:
            groups.append({
                "cn": entry.cn.value if "cn" in entry else None,
                "sAMAccountName": (
                    entry.sAMAccountName.value
                    if "sAMAccountName" in entry
                    else None
                ),
                "dn": (
                    entry.distinguishedName.value
                    if "distinguishedName" in entry
                    else None
                ),
                "description": (
                    entry.description.value
                    if "description" in entry
                    else None
                ),
                "members": (
                    entry.member.values
                    if "member" in entry
                    else []
                )
            })

        print(groups)

    finally:
        conn.unbind()