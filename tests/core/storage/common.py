# -*- coding: utf-8 -*-

# ################################################################### #
#                                                                     #
#  BigBrotherBot(B3) (www.bigbrotherbot.net)                          #
#  Copyright (C) 2005 Michael "ThorN" Thornton                        #
#                                                                     #
#  This program is free software; you can redistribute it and/or      #
#  modify it under the terms of the GNU General Public License        #
#  as published by the Free Software Foundation; either version 2     #
#  of the License, or (at your option) any later version.             #
#                                                                     #
#  This program is distributed in the hope that it will be useful,    #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of     #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the       #
#  GNU General Public License for more details.                       #
#                                                                     #
#  You should have received a copy of the GNU General Public License  #
#  along with this program; if not, write to the Free Software        #
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA      #
#  02110-1301, USA.                                                   #
#                                                                     #
# ################################################################### #

from b3.clients import Client
from b3.clients import Alias
from b3.clients import IpAlias
from b3.clients import Penalty
from b3.clients import Group
from mock import Mock
from mockito import when
from mockito import any as ANY

class StorageAPITest(object):

    storage = None
        
    def test_setClient(self):
        c1 = Client(ip="1.2.3.4", connections=2, guid="abcdefghijkl", pbid="123546abcdef", name="some dude", greeting="hi!", mask_level=20, group_bits=8, login="test login", password="test password")
        c1_id = self.storage.setClient(c1)
        self.assertEqual(1, c1_id)
        c2 = self.storage.getClient(Client(id=c1_id))
        self.assertIsInstance(c2, Client)
        self.assertEqual("1.2.3.4", c2.ip)
        self.assertEqual(2, c2.connections)
        self.assertEqual("abcdefghijkl", c2.guid)
        self.assertEqual("123546abcdef", c2.pbid)
        self.assertEqual("some dude", c2.name)
        self.assertEqual("hi!", c2.greeting)
        self.assertEqual("test login", c2.login)
        self.assertEqual("test password", c2.password)
        c3 = Client(id=c1_id, ip="5.6.7.8", connections=1, guid="ddddddddd", pbid="zzzzzzzzzzz", name="milka", greeting="hello")
        self.storage.setClient(c3)
        c4 = self.storage.getClient(Client(id=c1_id))
        self.assertIsInstance(c4, Client)
        self.assertEqual("5.6.7.8", c4.ip)
        self.assertEqual(1, c4.connections)
        self.assertEqual("ddddddddd", c4.guid)
        self.assertEqual("zzzzzzzzzzz", c4.pbid)
        self.assertEqual("milka", c4.name)
        self.assertEqual("hello", c4.greeting)

    # def test_setClient_no_db(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     c1 = Mock()
    #     c1.id = None
    #     self.assertRaises(KeyError, self.storage.setClient, c1)

    def test_getClient_id(self):
        c1 = Client(ip="1.2.3.4", connections=3, guid="mlkjmlkjqsdf", pbid="123546abcdef", name="some dude", greeting="hi!")
        c1_id = self.storage.setClient(c1)
        self.assertEqual(1, c1_id)
        c2 = self.storage.getClient(Client(id=c1_id))
        self.assertIsInstance(c2, Client)

    def test_getClient_guid(self):
        c1 = Client(ip="1.2.3.4", connections=3, guid="mlkjmlkjqsdf", pbid="123546abcdef", name="some dude", greeting="hi!")
        c1_id = self.storage.setClient(c1)
        self.assertEqual(1, c1_id)
        c2 = self.storage.getClient(Client(guid="mlkjmlkjqsdf"))
        self.assertIsInstance(c2, Client)
        self.assertRaises(KeyError, self.storage.getClient, Client(guid='god'))

    def test_getClientsMatching(self):
        self.storage.setClient(Client(ip="1.2.3.4", connections=2, guid="mlkjmlkjqsdf", pbid="123546abcdef", name="bill"))
        self.storage.setClient(Client(ip="4.2.3.5", connections=3, guid="azerazerazer", pbid="wxcvwxvcxwcv", name="john"))
        self.storage.setClient(Client(ip="4.2.3.5", connections=45, guid="rtyrtyrty", pbid="rtyrtyrrtyr", name="jack"))

        result = self.storage.getClientsMatching({'guid': "xxxxxxxxxx"})
        self.assertEqual(0, len(result))

        result = self.storage.getClientsMatching({'ip': "1.2.3.4"})
        self.assertEqual(1, len(result))
        self.assertEqual('bill', result[0].name)

        result = self.storage.getClientsMatching({'ip': "4.2.3.5"})
        self.assertEqual(2, len(result))

        result = self.storage.getClientsMatching({'pbid': "rtyrtyrrtyr"})
        self.assertEqual(1, len(result))
        self.assertEqual('jack', result[0].name)

        result = self.storage.getClientsMatching({'name': "jack"})
        self.assertEqual(1, len(result))
        self.assertEqual('jack', result[0].name)

        result = self.storage.getClientsMatching({'ip': "4.2.3.5", 'name': 'jack'})
        self.assertEqual(1, len(result))
        self.assertEqual('jack', result[0].name)

        result = self.storage.getClientsMatching({'ip': "4.2.3.5", 'connections >': 10})
        self.assertEqual(1, len(result))
        self.assertEqual('jack', result[0].name)

    # def test_getClientsMatching_no_db(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     self.assertRaises(KeyError, self.storage.getClientsMatching, {'guid': "xxxxxxxxxx"})

    def test_setClientAlias(self):
        alias_id1 = self.storage.setClientAlias(Alias(alias='bill', clientId=1))
        self.assertIsNotNone(alias_id1)
        alias_id2 = self.storage.setClientAlias(Alias(alias='joe', clientId=1))
        self.assertEqual(alias_id1 + 1, alias_id2)
        alias_id3 = self.storage.setClientAlias(Alias(id=alias_id1, alias='billy', clientId=1))
        self.assertIsNotNone(alias_id3)

    # def test_setClientAlias_no_db(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     alias = Mock()
    #     alias.id = None
    #     self.assertRaises(KeyError, self.storage.setClientAlias, alias)

    def test_getClientAlias(self):
        alias = Alias(alias='bill', timeAdd=12, timeEdit=654, numUsed=7, clientId=54)
        alias_id = self.storage.setClientAlias(alias)
        alias = self.storage.getClientAlias(Alias(id=alias_id))
        self.assertIsInstance(alias, Alias)
        self.assertEqual(alias.alias, 'bill')
        self.assertEqual(alias.timeAdd, 12)
        self.assertEqual(alias.timeEdit, 654)
        self.assertEqual(alias.numUsed, 7)
        self.assertEqual(alias.clientId, 54)
        alias2 = self.storage.getClientAlias(Alias(clientId=54, alias='bill'))
        self.assertEqual(alias.id, alias2.id)

    def test_getClientAlias_KeyError(self):
        alias = Mock()
        alias.id = 132
        self.assertRaises(KeyError, self.storage.getClientAlias, alias)

    def test_getClientAliases(self):
        client = Mock()
        client.id = 15
        self.storage.setClientAlias(Alias(alias='bill', clientId=client.id))
        self.storage.setClientAlias(Alias(alias='joe', clientId=client.id))
        self.storage.setClientAlias(Alias(alias='jack', clientId=0))
        aliases = self.storage.getClientAliases(client)
        self.assertIsInstance(aliases, list)
        self.assertEqual(len(aliases), 2)
        bucket = []
        for i in aliases:
            self.assertIsInstance(i, Alias)
            self.assertEqual(i.clientId, client.id)
            self.assertNotEqual(i.id, None)
            self.assertNotEqual(i.alias, None)
            self.assertNotEqual(i.timeAdd, None)
            self.assertNotEqual(i.timeEdit, None)
            self.assertNotEqual(i.numUsed, None)
            bucket.append(i.alias)
        self.assertIn('bill', bucket)
        self.assertIn('joe', bucket)
        self.assertNotIn('jack', bucket)

    # def test_getClientAliases_no_db(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     client = Mock()
    #     client.id = 15
    #     self.assertRaises(KeyError, self.storage.getClientAliases, client)

    def test_setClientIpAddress(self):
        ipalias_id1 = self.storage.setClientIpAddress(IpAlias(ip='1.2.3.4', clientId=1))
        self.assertIsNotNone(ipalias_id1)
        ipalias_id2 = self.storage.setClientIpAddress(IpAlias(ip='127.0.0.1', clientId=1))
        self.assertEqual(ipalias_id1 + 1, ipalias_id2)
        ipalias_id3 = self.storage.setClientIpAddress(IpAlias(id=ipalias_id1, ip='0.0.0.0', clientId=1))
        self.assertEqual(ipalias_id1, ipalias_id3)
    
    # def test_setClientIpAddress_no_db(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     ipalias = Mock()
    #     ipalias.id = None
    #     self.assertRaises(KeyError, self.storage.setClientIpAddress, ipalias)

    def test_getClientIpAddress(self):
        ipalias = IpAlias(ip='88.44.55.22', timeAdd=12, timeEdit=654, numUsed=7, clientId=54)
        ipalias_id = self.storage.setClientIpAddress(ipalias)
        ipalias = self.storage.getClientIpAddress(IpAlias(id=ipalias_id))
        self.assertIsInstance(ipalias, IpAlias)
        self.assertEqual(ipalias.ip, '88.44.55.22')
        self.assertEqual(ipalias.timeAdd, 12)
        self.assertEqual(ipalias.timeEdit, 654)
        self.assertEqual(ipalias.numUsed, 7)
        self.assertEqual(ipalias.clientId, 54)
        ipalias2 = self.storage.getClientIpAddress(IpAlias(clientId=ipalias.clientId, ip=ipalias.ip))
        self.assertEqual(ipalias.id, ipalias2.id)

    # def test_getClientIpAddress_no_db(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     client = Mock()
    #     client.id = 15
    #     self.assertRaises(KeyError, self.storage.getClientIpAddress, client)

    def test_getClientIpAddresses(self):
        client = Mock()
        client.id = 15
        self.storage.setClientIpAddress(IpAlias(ip='44.44.44.44', clientId=client.id))
        self.storage.setClientIpAddress(IpAlias(ip='55.55.55.55', clientId=client.id))
        self.storage.setClientIpAddress(IpAlias(ip='66.66.66.66', clientId=0))
        ipaliases = self.storage.getClientIpAddresses(client)
        self.assertIsInstance(ipaliases, list)
        self.assertEqual(len(ipaliases), 2)
        ips = []
        for i in ipaliases:
            self.assertIsInstance(i, IpAlias)
            self.assertEqual(i.clientId, client.id)
            self.assertNotEqual(i.id, None)
            self.assertNotEqual(i.ip, None)
            self.assertNotEqual(i.timeAdd, None)
            self.assertNotEqual(i.timeEdit, None)
            self.assertNotEqual(i.numUsed, None)
            ips.append(i.ip)
        self.assertIn('44.44.44.44', ips)
        self.assertIn('55.55.55.55', ips)
        self.assertNotIn('66.66.66.66', ips)
        
    # def test_getClientIpAddresses_no_db(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     client = Mock()
    #     client.id = 15
    #     self.assertRaises(KeyError, self.storage.getClientIpAddresses, client)

    def test_getLastPenalties(self):
        c1 = Mock()
        c1.id = 15
        c2 = Mock()
        c2.id = 18
        Penalty(clientId=c1.id, adminId=0, inactive=1, type='Ban', timeExpire=-1, data=u'pA').save(self.console)
        Penalty(clientId=c1.id, adminId=0, inactive=0, type='Ban', timeExpire=self.console.time()+10, data=u'pB').save(self.console)
        Penalty(clientId=c1.id, adminId=0, inactive=0, type='Warning', timeExpire=self.console.time()+10, data=u'pC').save(self.console)
        Penalty(clientId=c1.id, adminId=0, inactive=0, type='Kick', timeExpire=self.console.time()-10, data=u'pD').save(self.console)
        Penalty(clientId=c1.id, adminId=0, inactive=0, type='Ban', timeExpire=self.console.time()-10, data=u'pE').save(self.console)
        Penalty(clientId=c2.id, adminId=0, inactive=0, type='Warning', timeExpire=-1, data=u'pF').save(self.console)
        Penalty(clientId=c2.id, adminId=0, inactive=0, type='TempBan', timeExpire=-1, data=u'pG').save(self.console)
        Penalty(clientId=c2.id, adminId=0, inactive=0, type='Ban', timeExpire=-1, data=u'pH').save(self.console)

        def getLastPenalties(types, num):
            p_datas = []
            for p in self.storage.getLastPenalties(types=types, num=num):
                p_datas.append(p.data)
                self.assertTrue(p.inactive == 0)
                self.assertTrue(p.timeExpire == -1 or p.timeExpire > self.console.time())
            self.assertGreaterEqual(num, len(p_datas))
            return p_datas

        self.assertListEqual([u'pH', u'pG', u'pF', u'pC', u'pB'], getLastPenalties(types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), num=5))
        self.assertListEqual([u'pH', u'pG', u'pF', u'pC'], getLastPenalties(types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), num=4))
        self.assertListEqual([u'pH', u'pG', u'pB'], getLastPenalties(types=('Ban', 'TempBan'), num=5))

    def test_setClientPenalty(self):
        id1 = self.storage.setClientPenalty(Penalty(type='Ban', clientId=1, adminId=0))
        self.assertIsNotNone(id1)
        id2 = self.storage.setClientPenalty(Penalty(type='Kick', clientId=1, adminId=0))
        self.assertEqual(id1 + 1, id2)
        id3 = self.storage.setClientPenalty(Penalty(id=id1, type='Warning', clientId=1, adminId=0))
        self.assertEqual(id1, id3)

    def test_setClientPenalty_bad_keyword(self):
        id1 = self.storage.setClientPenalty(Penalty(keyword='!=+', clientId=1, adminId=0))
        self.assertIsNotNone(id1)
        p1 = self.storage.getClientPenalty(Penalty(id=id1, type='foo'))
        self.assertIsInstance(p1, Penalty)
        self.assertIs(type(p1), Penalty)
        self.assertEquals('', p1.keyword)

    # def test_setClientPenalty_no_db(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     p1 = Mock(spec=Penalty)
    #     p1.id = None
    #     p1.keyword = 'test'
    #     self.assertRaises(KeyError, self.storage.setClientPenalty, p1)

    def test_getClientPenalty(self):
        tmp = Penalty(type='Kick', 
                      clientId=54,
                      inactive=1,
                      adminId=4,
                      reason='respect the rules',
                      keyword='rules',
                      data='foo',
                      timeAdd=123,
                      timeEdit=1234,
                      timeExpire=654,
                      duration=87,
                      )
        tmp_id = self.storage.setClientPenalty(tmp)
        penalty = self.storage.getClientPenalty(Penalty(type="Kick", id=tmp_id))
        self.assertIsInstance(penalty, Penalty)
        self.assertEqual(penalty.type, 'Kick')
        self.assertEqual(penalty.clientId, 54)
        self.assertEqual(penalty.inactive, 1)
        self.assertEqual(penalty.adminId, 4)
        self.assertEqual(penalty.reason, 'respect the rules')
        self.assertEqual(penalty.keyword, 'rules')
        self.assertEqual(penalty.data, 'foo')
        self.assertEqual(penalty.timeAdd, 123)
        self.assertEqual(penalty.timeEdit, 1234)
        self.assertEqual(penalty.timeExpire, 654)
        self.assertEqual(penalty.duration, 87)
        self.assertRaises(KeyError, self.storage.getClientPenalty, Penalty(id=654654))

    def test_getClientPenalties(self):
        c1 = Mock()
        c1.id = 15
        c2 = Mock()
        c2.id = 18
        Penalty(clientId=c1.id, adminId=0, inactive=1, type='Ban', timeExpire=-1, data='pA').save(self.console)
        Penalty(clientId=c1.id, adminId=0, inactive=0, type='Ban', timeExpire=self.console.time()+10, data='pB').save(self.console)
        Penalty(clientId=c1.id, adminId=0, inactive=0, type='Warning', timeExpire=self.console.time()+10, data='pC').save(self.console)
        Penalty(clientId=c1.id, adminId=0, inactive=0, type='Kick', timeExpire=self.console.time()-10, data='pD').save(self.console)
        Penalty(clientId=c1.id, adminId=0, inactive=0, type='Ban', timeExpire=self.console.time()-10, data='pE').save(self.console)
        Penalty(clientId=c2.id, adminId=0, inactive=0, type='Warning', timeExpire=-1, data='pF').save(self.console)
        Penalty(clientId=c2.id, adminId=0, inactive=0, type='TempBan', timeExpire=-1, data='pG').save(self.console)

        def assertPenalties(client, types, penalties_in=[], penalties_notin=[]):
            penalties = self.storage.getClientPenalties(client=client, type=types)
            self.assertIsInstance(penalties, list)
            bucket = []
            for i in penalties:
                self.assertIsInstance(i, Penalty)
                self.assertEqual(i.clientId, client.id)
                bucket.append(i.data)
            for i in penalties_in:
                self.assertIn(i, bucket)
            for i in penalties_notin:
                self.assertNotIn(i, bucket)

        assertPenalties(client=c1, types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), penalties_in=('pB','pC'), penalties_notin=('pA','pD','pE','pF','pG'))
        assertPenalties(client=c2, types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), penalties_in=('pF','pG'), penalties_notin=('pA','pB','pC','pD','pE'))

        # when(self.storage).query(ANY()).thenRaise(KeyError())
        # self.assertRaises(KeyError, self.storage.getClientPenalties, c1)

    def test_getClientLastPenalty(self):
        client = Mock()
        client.id = 15
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=2, timeExpire=-1, type='Ban', data='pA'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=4, timeExpire=-1, type='Kick',data='pB'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=1, timeExpire=-1, type='Notice', data='pC'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=3, timeExpire=-1, type='Ban', data='pD'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=6, timeExpire=-1, type='Kick', data='pE'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=5, timeExpire=-1, type='Ban', data='pF'))
        penalty = self.storage.getClientLastPenalty(client=client)
        self.assertIsInstance(penalty, Penalty)
        self.assertEqual(penalty.data, 'pF')
        penalty = self.storage.getClientLastPenalty(client=client, type=('Ban', 'Kick'))
        self.assertIsInstance(penalty, Penalty)
        self.assertEqual(penalty.data, 'pE')
        penalty = self.storage.getClientLastPenalty(client=client, type=('Ban', 'Kick','Notice'))
        self.assertIsInstance(penalty, Penalty)
        self.assertEqual(penalty.data, 'pE')
        self.assertIsNone(self.storage.getClientLastPenalty(Penalty(clientId=3231)))

    def test_getClientFirstPenalty(self):
        client = Mock()
        client.id = 15
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=2, timeExpire=-1, type='Ban', data='pA'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=4, timeExpire=-1, type='Kick', data='pB'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=1, timeExpire=-1, type='Notice', data='pC'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=3, timeExpire=-1, type='Ban', data='pD'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=6, timeExpire=-1, type='Kick', data='pE'))
        self.storage.setClientPenalty(Penalty(clientId=client.id, adminId=0, timeAdd=5, timeExpire=-1, type='Ban', data='pF'))
        penalty = self.storage.getClientFirstPenalty(client=client)
        self.assertIsInstance(penalty, Penalty)
        self.assertEqual(penalty.data, 'pA')
        penalty = self.storage.getClientFirstPenalty(client=client, type=('Ban', 'Kick'))
        self.assertIsInstance(penalty, Penalty)
        self.assertEqual(penalty.data, 'pA')
        penalty = self.storage.getClientFirstPenalty(client=client, type=('Ban', 'Kick','Notice'))
        self.assertIsInstance(penalty, Penalty)
        self.assertEqual(penalty.data, 'pC')
        self.assertIsNone(self.storage.getClientFirstPenalty(Penalty(clientId=3231)))

    def test_disableClientPenalties(self):
        c1 = Mock()
        c1.id = 15
        c2 = Mock()
        c2.id = 18
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='Ban', inactive=1, data='pA').save(self.console)
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='Ban', inactive=0, data='pB').save(self.console)
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='Warning', inactive=0, data='pC').save(self.console)
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='Kick', inactive=0, data='pD').save(self.console)
        Penalty(clientId=c2.id, adminId=0, timeExpire=-1, type='Notice', inactive=0, data='pE').save(self.console)
        Penalty(clientId=c2.id, adminId=0, timeExpire=-1, type='Warning', inactive=0, data='pF').save(self.console)
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='TempBan', inactive=0, data='pG').save(self.console)

        def assertPenalties(client, types='Ban', penalties_in=[], penalties_notin=[]):
            penalties = self.storage.getClientPenalties(client=client, type=types)
            self.assertIsInstance(penalties, list)
            bucket = []
            for i in penalties:
                self.assertIsInstance(i, Penalty)
                self.assertEqual(i.clientId, client.id)
                bucket.append(i.data)
            for i in penalties_in:
                self.assertIn(i, bucket)
            for i in penalties_notin:
                self.assertNotIn(i, bucket)

        assertPenalties(client=c1, types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), penalties_in=('pB','pC','pD','pG'), penalties_notin=('pA','pE','pF'))
        assertPenalties(client=c2, types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), penalties_in=('pE','pF'), penalties_notin=('pA','pB','pC','pD','pG'))

        self.storage.disableClientPenalties(client=c1)
        assertPenalties(client=c1, types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), penalties_in=('pC','pD','pG'), penalties_notin=('pA','pB','pE','pF'))
        assertPenalties(client=c2, types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), penalties_in=('pE','pF'), penalties_notin=('pA','pB','pC','pD','pG'))

        self.storage.disableClientPenalties(client=c1, type=('Kick','Notice'))
        assertPenalties(client=c1, types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'), penalties_in=('pC','pG'), penalties_notin=('pA','pB','pD','pE','pF'))
        assertPenalties(client=c2, types=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice'),  penalties_in=('pE','pF'), penalties_notin=('pA','pB','pC','pD','pG'))

    def test_numPenalties(self):
        c1 = Mock()
        c1.id = 15
        c2 = Mock()
        c2.id = 18
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='Ban', inactive=1, data='pA').save(self.console)
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='Ban', inactive=0, data='pB').save(self.console)
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='Warning', inactive=0, data='pC').save(self.console)
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='Kick', inactive=0, data='pD').save(self.console)
        Penalty(clientId=c2.id, adminId=0, timeExpire=-1, type='Notice', inactive=0, data='pE').save(self.console)
        Penalty(clientId=c2.id, adminId=0, timeExpire=-1, type='Warning', inactive=0, data='pF').save(self.console)
        Penalty(clientId=c1.id, adminId=0, timeExpire=-1, type='TempBan', inactive=0, data='pG').save(self.console)
        self.assertEqual(1, self.storage.numPenalties(client=c1))
        self.assertEqual(4, self.storage.numPenalties(client=c1, type=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice')))
        self.assertEqual(0, self.storage.numPenalties(client=c2))
        self.assertEqual(2, self.storage.numPenalties(client=c2, type=('Ban', 'TempBan', 'Kick', 'Warning', 'Notice')))

        # when(self.storage).query(ANY()).thenRaise(KeyError())
        # self.assertRaises(KeyError, self.storage.numPenalties, c1)

    def test_getGroups(self):
        groups = self.storage.getGroups()
        self.assertEqual(8, len(groups))
        for g in groups:
            self.assertIsInstance(g, Group)
    
    # def test_getGroups_unknown(self):
    #     when(self.storage).query(ANY()).thenRaise(KeyError())
    #     self.assertRaises(KeyError, self.storage.getGroups)

    def test_getGroup_by_keyword(self):
        g = self.storage.getGroup(Group(keyword='superadmin'))
        self.assertIsInstance(g, Group)
        self.assertEquals('superadmin', g.keyword)
        self.assertEquals(100, g.level)
        self.assertRaises(KeyError, self.storage.getGroup, Group(keyword='foo'))

    def test_getGroup_by_level(self):
        g = self.storage.getGroup(Group(level='20'))
        self.assertIsInstance(g, Group)
        self.assertEquals('mod', g.keyword)
        self.assertEquals(20, g.level)
        self.assertRaises(KeyError, self.storage.getGroup, Group(level='500'))

    def test_getGroup_none(self):
        try:
            self.storage.getGroup(None)
            self.fail("expecting KeyError")
        except KeyError:
            pass
        except Exception:
            self.fail("expecting KeyError")

    def test_getGroup_junk(self):
        try:
            self.storage.getGroup(5)
            self.fail("expecting KeyError")
        except KeyError:
            pass
        except Exception:
            self.fail("expecting KeyError")

    def test_getGroup_bad_group(self):
        try:
            self.storage.getGroup(Group(level=-1))
            self.fail("expecting KeyError")
        except KeyError:
            pass
        except Exception:
            self.fail("expecting KeyError")

    def test_getCounts(self):
        c1 = Client(guid="aaaaaaaaa")
        self.assertEqual({'Kicks': 0, 'TempBans': 0, 'clients': 0, 'Bans': 0, 'Warnings': 0}, self.storage.getCounts())
        self.storage.setClient(c1)
        self.assertEqual({'Kicks': 0, 'TempBans': 0, 'clients': 1, 'Bans': 0, 'Warnings': 0}, self.storage.getCounts())
        self.storage.setClient(Client(guid="bbbbbbbbbb"))
        self.assertEqual({'Kicks': 0, 'TempBans': 0, 'clients': 2, 'Bans': 0, 'Warnings': 0}, self.storage.getCounts())
        Penalty(clientId=c1.id, adminId=0, type='Ban').save(self.console)
        self.assertEqual({'Kicks': 0, 'TempBans': 0, 'clients': 2, 'Bans': 1, 'Warnings': 0}, self.storage.getCounts())
        Penalty(clientId=c1.id, adminId=0, type='Ban').save(self.console)
        self.assertEqual({'Kicks': 0, 'TempBans': 0, 'clients': 2, 'Bans': 2, 'Warnings': 0}, self.storage.getCounts())
        Penalty(clientId=c1.id, adminId=0, type='TempBan').save(self.console)
        self.assertEqual({'Kicks': 0, 'TempBans': 1, 'clients': 2, 'Bans': 2, 'Warnings': 0}, self.storage.getCounts())
        Penalty(clientId=c1.id, adminId=0, type='Kick').save(self.console)
        self.assertEqual({'Kicks': 1, 'TempBans': 1, 'clients': 2, 'Bans': 2, 'Warnings': 0}, self.storage.getCounts())
        Penalty(clientId=c1.id, adminId=0, type='Warning').save(self.console)
        self.assertEqual({'Kicks': 1, 'TempBans': 1, 'clients': 2, 'Bans': 2, 'Warnings': 1}, self.storage.getCounts())

    def test_truncateTables_single_table(self):
        self.storage.setClient(Client(guid="aaaaaaaaa"))
        self.storage.setClient(Client(guid="bbbbbbbbb"))
        cursor = self.storage.query("SELECT * FROM clients")
        self.assertFalse(cursor.EOF)
        self.storage.truncateTable('clients')
        cursor = self.storage.query("SELECT * FROM clients")
        self.assertTrue(cursor.EOF)

    def test_truncateTables_multiple_tables(self):
        c1 = Client(guid="aaaaaaaaa")
        c2 = Client(guid="bbbbbbbbb")
        self.storage.setClient(c1)
        self.storage.setClient(c2)
        self.storage.setClientPenalty(Penalty(clientId=c1.id, adminId=0, type='Kick'))
        self.storage.setClientPenalty(Penalty(clientId=c2.id, adminId=0, type='Kick'))
        cursor = self.storage.query("SELECT * FROM clients")
        self.assertFalse(cursor.EOF)
        cursor = self.storage.query("SELECT * FROM penalties")
        self.assertFalse(cursor.EOF)
        self.storage.truncateTable(['clients', 'penalties'])
        cursor = self.storage.query("SELECT * FROM clients")
        self.assertTrue(cursor.EOF)
        cursor = self.storage.query("SELECT * FROM penalties")
        self.assertTrue(cursor.EOF)

    def test_truncateTables_invalid_table_name(self):
        self.assertRaises(KeyError, self.storage.truncateTable, 'invalid_table')
        self.assertRaises(KeyError, self.storage.truncateTable, ['invalid_table1', ['invalid_table2']])