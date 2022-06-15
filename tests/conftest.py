# ==================================================================================
#       Copyright (c) 2019 Nokia
#       Copyright (c) 2018-2019 AT&T Intellectual Property.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
import pytest

from ricxappframe.entities.rnib.nb_identity_pb2 import NbIdentity
from ricxappframe.entities.rnib.cell_pb2 import Cell
import ricxappframe.entities.rnib.nb_identity_pb2 as pb_nb
import ricxappframe.entities.rnib.nodeb_info_pb2 as pb_nbi
import ricxappframe.entities.rnib.enb_pb2 as pb_enb
import ricxappframe.entities.rnib.gnb_pb2 as pb_gnb
import ricxappframe.entities.rnib.cell_pb2 as pb_cell
import ricxappframe.entities.rnib.ran_function_pb2 as pb_rf


# These are here just to reduce the size of the code in test_rmr so those (important) tests are more readable; in theory these dicts could be large
# The actual value of the constants should be ignored by the tests; all we should care
# about is that the constant value was returned by the RMR function. Further, we should
# not consider it an error if RMR returns more than what is listed here; these are the
# list of what is/could be used by this package.
@pytest.fixture
def expected_constants():
    return {
        "RMR_MAX_XID": 32,
        "RMR_MAX_SID": 32,
        "RMR_MAX_MEID": 32,
        "RMR_MAX_SRC": 64,
        "RMR_MAX_RCV_BYTES": 4096,
        "RMRFL_NONE": 0,
        "RMRFL_MTCALL": 2,  # can't be added here until jenkins version >= 1.8.3
        "RMRFL_AUTO_ALLOC": 3,
        "RMR_DEF_SIZE": 0,
        "RMR_VOID_MSGTYPE": -1,
        "RMR_VOID_SUBID": -1,
        "RMR_OK": 0,
        "RMR_ERR_BADARG": 1,
        "RMR_ERR_NOENDPT": 2,
        "RMR_ERR_EMPTY": 3,
        "RMR_ERR_NOHDR": 4,
        "RMR_ERR_SENDFAILED": 5,
        "RMR_ERR_CALLFAILED": 6,
        "RMR_ERR_NOWHOPEN": 7,
        "RMR_ERR_WHID": 8,
        "RMR_ERR_OVERFLOW": 9,
        "RMR_ERR_RETRY": 10,
        "RMR_ERR_RCVFAILED": 11,
        "RMR_ERR_TIMEOUT": 12,
        "RMR_ERR_UNSET": 13,
        "RMR_ERR_TRUNC": 14,
        "RMR_ERR_INITFAILED": 15,
    }


@pytest.fixture
def expected_states():
    return {
        0: "RMR_OK",
        1: "RMR_ERR_BADARG",
        2: "RMR_ERR_NOENDPT",
        3: "RMR_ERR_EMPTY",
        4: "RMR_ERR_NOHDR",
        5: "RMR_ERR_SENDFAILED",
        6: "RMR_ERR_CALLFAILED",
        7: "RMR_ERR_NOWHOPEN",
        8: "RMR_ERR_WHID",
        9: "RMR_ERR_OVERFLOW",
        10: "RMR_ERR_RETRY",
        11: "RMR_ERR_RCVFAILED",
        12: "RMR_ERR_TIMEOUT",
        13: "RMR_ERR_UNSET",
        14: "RMR_ERR_TRUNC",
        15: "RMR_ERR_INITFAILED",
    }


@pytest.fixture
def rnib_information():
    rnib1 = NbIdentity()
    rnib1.inventory_name = "nodeb_1234"
    rnib1.global_nb_id.plmn_id = "plmn_1234"
    rnib1.global_nb_id.nb_id = "nb_1234"
    rnib1.connection_status = 1

    rnib2 = NbIdentity()
    rnib1.inventory_name = "nodeb_5678"
    rnib1.global_nb_id.plmn_id = "plmn_5678"
    rnib1.global_nb_id.nb_id = "nb_5678"
    rnib1.connection_status = 6

    return [rnib1.SerializeToString(), rnib2.SerializeToString()]


@pytest.fixture
def rnib_cellinformation():
    rnib_cell1 = Cell()
    print(rnib_cell1)
    rnib_cell1.type = Cell.LTE_CELL

    rnib_cell2 = Cell()
    rnib_cell2.type = Cell.LTE_CELL

    return [rnib_cell2.SerializeToString(), rnib_cell2.SerializeToString()]


def createRanFunction(ran_function_id, definition, revision, oid):
    r = pb_rf.RanFunction()
    r.ran_function_id = ran_function_id
    r.ran_function_definition = definition
    r.ran_function_revision = revision
    r.ran_function_oid = oid
    return r


def createServedCellInfo(pci, cell_id, tac):
    s = pb_enb.ServedCellInfo()
    s.pci = pci
    s.cell_id = cell_id
    s.tac = tac
    return s


def createServedNRCellInfo(pci, cell_id, tac):
    s = pb_gnb.ServedNRCell()
#    s = pb_gnb.ServedNRCellInformation()
    s.served_nr_cell_information.nr_pci = pci
    s.served_nr_cell_information.cell_id = cell_id
    s.served_nr_cell_information.stac5g = tac
    s.served_nr_cell_information.nr_mode = 2
    return s


class rnibHelpers:
    @staticmethod
    def createNodeb(name, plmn, nbid):
        nb = pb_nb.NbIdentity()
        nb.inventory_name = name
        nb.global_nb_id.plmn_id = plmn
        nb.global_nb_id.nb_id = nbid
        nb.connection_status = 1
        return nb

    @staticmethod
    def createNodebInfo(name, nbtype, ip, port):
        nbi = pb_nbi.NodebInfo()
        nbi.ip = ip
        nbi.port = port
        nbi.e2_application_protocol = 1
        nbi.connection_status = 1
        if nbtype == 'GNB':
            nbi.node_type = 2
            rf1 = createRanFunction(1, b'te524367153', 1, "1.3.6.1.4.1.1.2.2.1")
            rf2 = createRanFunction(1, b'te524367153', 1, "1.3.6.1.4.1.1.2.2.2")
            rf3 = createRanFunction(1, b'te524367153', 1, "1.3.6.1.4.1.1.2.2.3")
            nbi.gnb.ran_functions.extend([rf1, rf2, rf3])
            s1 = createServedNRCellInfo(1, b'822', b'1452')
            s2 = createServedNRCellInfo(2, b'823', b'1453')
            s3 = createServedNRCellInfo(3, b'824', b'1454')
            nbi.gnb.served_nr_cells.extend([s1, s2, s3])
        else:
            nbi.node_type = 1
            nbi.enb.enb_type = 1
            s1 = createServedCellInfo(1, b'822', b'1452')
            s2 = createServedCellInfo(2, b'823', b'1453')
            s3 = createServedCellInfo(3, b'824', b'1454')
            nbi.enb.served_cells.extend([s1, s2, s3])
        return nbi

    @staticmethod
    def createCell(name, pci):
        c = pb_cell.Cell()
        c.type = pb_cell.Cell.Type.Value('LTE_CELL')
#        print(pb_cell.Cell.Type.Name(pb_cell.Cell.LTE_CELL))
        c.served_cell_info.pci = pci
        c.served_cell_info.cell_id = b'822'
        c.served_cell_info.tac = b'1452'
        return c


@pytest.fixture
def rnib_helpers():
    return rnibHelpers
