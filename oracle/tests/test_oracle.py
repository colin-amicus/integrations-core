# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

import mock
import pytest


def test__get_connection_instant_client(check, instance):
    """
    Test the _get_connection method using the instant client
    """
    check.use_oracle_client = True
    server, user, password, service, jdbc_driver, _, _ = check._get_config(instance)
    con = mock.MagicMock()
    service_check = mock.MagicMock()
    check.service_check = service_check
    expected_tags = ['server:localhost:1521', 'optional:tag1']
    with mock.patch('datadog_checks.oracle.oracle.cx_Oracle') as cx:
        cx.connect.return_value = con
        ret = check._get_connection(server, user, password, service, jdbc_driver, expected_tags)
        assert ret == con
        cx.connect.assert_called_with('system/oracle@//localhost:1521/xe')
        service_check.assert_called_with(check.SERVICE_CHECK_NAME, check.OK, tags=expected_tags)


def test__get_connection_jdbc(check, instance):
    """
    Test the _get_connection method using the JDBC client
    """
    check.use_oracle_client = False
    server, user, password, service, jdbc_driver, _, _ = check._get_config(instance)
    con = mock.MagicMock()
    service_check = mock.MagicMock()
    check.service_check = service_check
    expected_tags = ['server:localhost:1521', 'optional:tag1']
    with mock.patch('datadog_checks.oracle.oracle.cx_Oracle') as cx:
        cx.DatabaseError = RuntimeError
        cx.clientversion.side_effect = cx.DatabaseError()
        with mock.patch('datadog_checks.oracle.oracle.jdb') as jdb:
            with mock.patch('datadog_checks.oracle.oracle.jpype') as jpype:
                jpype.isJVMStarted.return_value = False
                jdb.connect.return_value = con
                ret = check._get_connection(server, user, password, service, jdbc_driver, expected_tags)
                assert ret == con
                jdb.connect.assert_called_with(
                    'oracle.jdbc.OracleDriver', 'jdbc:oracle:thin:@//localhost:1521/xe', ['system', 'oracle'], None
                )
                service_check.assert_called_with(check.SERVICE_CHECK_NAME, check.OK, tags=expected_tags)


def test__get_connection_failure(check, instance):
    """
    Test the right service check is sent upon _get_connection failures
    """
    expected_tags = ['server:localhost:1521', 'optional:tag1']
    service_check = mock.MagicMock()
    check.service_check = service_check
    server, user, password, service, jdbc_driver, _, _ = check._get_config(instance)
    with pytest.raises(Exception):
        check._get_connection(server, user, password, service, jdbc_driver, expected_tags)
    service_check.assert_called_with(check.SERVICE_CHECK_NAME, check.CRITICAL, tags=expected_tags)
