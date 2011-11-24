# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2011 Courgette
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
"""
This test is about testing the setup feature which downloads a plugin zip file
and extract it in the correct directory of the B3 installation in the case
the plugin is not composed of a single python file module but instead of a
python module defined as a folder. (example the metabans plugin)
"""
import os
import shutil
from b3.setup import Setup
import unittest
from mock import Mock, patch # http://www.voidspace.org.uk/python/mock/

import urllib2

import tempfile
tmp_dir = os.path.join(tempfile.gettempdir(), "download_test")
mocked_getAbsolutePath = Mock(return_value=tmp_dir)

# this is the base64 representation of a zip file containing the same structure as the metbans plugin
metaban_zip_base64_content = """UEsDBBQAAAAAADkubD8AAAAAAAAAAAAAAAAJAAAAbWV0YWJhbnMvUEsDBBQAAAAAAPctbD8AAAAA
AAAAAAAAAAAtAAAAbWV0YWJhbnMvY291cmdldHRlLWIzLXBsdWdpbi1tZXRhYmFucy14eHh4eHgv
UEsDBBQAAAAAAPctbD8AAAAAAAAAAAAAAAA4AAAAbWV0YWJhbnMvY291cmdldHRlLWIzLXBsdWdp
bi1tZXRhYmFucy14eHh4eHgvZXh0cGx1Z2lucy9QSwMEFAAAAAAA9y1sPwAAAAAAAAAAAAAAAD0A
AABtZXRhYmFucy9jb3VyZ2V0dGUtYjMtcGx1Z2luLW1ldGFiYW5zLXh4eHh4eC9leHRwbHVnaW5z
L2NvbmYvUEsDBAoAAAAAACQubD8AAAAAAAAAAAAAAABQAAAAbWV0YWJhbnMvY291cmdldHRlLWIz
LXBsdWdpbi1tZXRhYmFucy14eHh4eHgvZXh0cGx1Z2lucy9jb25mL3BsdWdpbl9tZXRhYmFucy54
bWxQSwMEFAAAAAAAMy5sPwAAAAAAAAAAAAAAAEEAAABtZXRhYmFucy9jb3VyZ2V0dGUtYjMtcGx1
Z2luLW1ldGFiYW5zLXh4eHh4eC9leHRwbHVnaW5zL21ldGFiYW5zL1BLAwQKAAAAAAATLmw/AAAA
AAAAAAAAAAAATAAAAG1ldGFiYW5zL2NvdXJnZXR0ZS1iMy1wbHVnaW4tbWV0YWJhbnMteHh4eHh4
L2V4dHBsdWdpbnMvbWV0YWJhbnMvc29tZWZpbGUucHlQSwMECgAAAAAAEy5sPwAAAAAAAAAAAAAA
AEwAAABtZXRhYmFucy9jb3VyZ2V0dGUtYjMtcGx1Z2luLW1ldGFiYW5zLXh4eHh4eC9leHRwbHVn
aW5zL21ldGFiYW5zL19faW5pdF9fLnB5UEsDBAoAAAAAAAIubD+wAF6zEAAAABAAAAA3AAAAbWV0
YWJhbnMvY291cmdldHRlLWIzLXBsdWdpbi1tZXRhYmFucy14eHh4eHgvcmVhZG1lLnR4dE1ldGFi
YW5zIHBsdWdpbiBQSwECPwAUAAAAAAA5Lmw/AAAAAAAAAAAAAAAACQAkAAAAAAAAABAAAAAAAAAA
bWV0YWJhbnMvCgAgAAAAAAABABgAcdOSgfagzAFx05KB9qDMAcCoaDj2oMwBUEsBAj8AFAAAAAAA
9y1sPwAAAAAAAAAAAAAAAC0AJAAAAAAAAAAQAAAAJwAAAG1ldGFiYW5zL2NvdXJnZXR0ZS1iMy1w
bHVnaW4tbWV0YWJhbnMteHh4eHh4LwoAIAAAAAAAAQAYAPdOdzj2oMwB9053OPagzAElTm449qDM
AVBLAQI/ABQAAAAAAPctbD8AAAAAAAAAAAAAAAA4ACQAAAAAAAAAEAAAAHIAAABtZXRhYmFucy9j
b3VyZ2V0dGUtYjMtcGx1Z2luLW1ldGFiYW5zLXh4eHh4eC9leHRwbHVnaW5zLwoAIAAAAAAAAQAY
ACPJfjj2oMwBI8l+OPagzAH3Tnc49qDMAVBLAQI/ABQAAAAAAPctbD8AAAAAAAAAAAAAAAA9ACQA
AAAAAAAAEAAAAMgAAABtZXRhYmFucy9jb3VyZ2V0dGUtYjMtcGx1Z2luLW1ldGFiYW5zLXh4eHh4
eC9leHRwbHVnaW5zL2NvbmYvCgAgAAAAAAABABgASRJ4OPagzAFJEng49qDMARiddzj2oMwBUEsB
Aj8ACgAAAAAAJC5sPwAAAAAAAAAAAAAAAFAAJAAAAAAAAAAgAAAAIwEAAG1ldGFiYW5zL2NvdXJn
ZXR0ZS1iMy1wbHVnaW4tbWV0YWJhbnMteHh4eHh4L2V4dHBsdWdpbnMvY29uZi9wbHVnaW5fbWV0
YWJhbnMueG1sCgAgAAAAAAABABgAZZSEaPagzAEAyUgE85bMAQDJSATzlswBUEsBAj8AFAAAAAAA
My5sPwAAAAAAAAAAAAAAAEEAJAAAAAAAAAAQAAAAkQEAAG1ldGFiYW5zL2NvdXJnZXR0ZS1iMy1w
bHVnaW4tbWV0YWJhbnMteHh4eHh4L2V4dHBsdWdpbnMvbWV0YWJhbnMvCgAgAAAAAAABABgAq69D
evagzAGrr0N69qDMASPJfjj2oMwBUEsBAj8ACgAAAAAAEy5sPwAAAAAAAAAAAAAAAEwAJAAAAAAA
AAAgAAAA8AEAAG1ldGFiYW5zL2NvdXJnZXR0ZS1iMy1wbHVnaW4tbWV0YWJhbnMteHh4eHh4L2V4
dHBsdWdpbnMvbWV0YWJhbnMvc29tZWZpbGUucHkKACAAAAAAAAEAGADV/5dW9qDMAeKFeHj2oMwB
431gXPagzAFQSwECPwAKAAAAAAATLmw/AAAAAAAAAAAAAAAATAAkAAAAAAAAACAAAABaAgAAbWV0
YWJhbnMvY291cmdldHRlLWIzLXBsdWdpbi1tZXRhYmFucy14eHh4eHgvZXh0cGx1Z2lucy9tZXRh
YmFucy9fX2luaXRfXy5weQoAIAAAAAAAAQAYANX/l1b2oMwBAMlIBPOWzAEAyUgE85bMAVBLAQI/
AAoAAAAAAAIubD+wAF6zEAAAABAAAAA3ACQAAAAAAAAAIAAAAMQCAABtZXRhYmFucy9jb3VyZ2V0
dGUtYjMtcGx1Z2luLW1ldGFiYW5zLXh4eHh4eC9yZWFkbWUudHh0CgAgAAAAAAABABgAvGhTQvag
zAEAyUgE85bMAQDJSATzlswBUEsFBgAAAAAJAAkA7QQAACkDAAAAAA=="""

fake_download_url = "qsdfqsdfqdsfsf"

# this will trick urllib2 into returning our base64 zip file instead of downloading something of the network
urlopen_response = Mock()
urlopen_response.url = fake_download_url
urlopen_response.info = Mock(return_value={})
urlopen_response.read = Mock(return_value= metaban_zip_base64_content.decode('base64'))


class Test_download(unittest.TestCase):

    def setUp(self):
        # create a tmp dir that the code under test will use to work
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        # disable whatever is done in the Setup constructor
        Setup.__init__ = object.__init__

    def tearDown(self):
        # cleaning
        shutil.rmtree(tmp_dir, ignore_errors=True)
        
    # those 2 decorators will replace some methods with mocks that we have control over
    # that way we know exactly what is to be expected
    @patch.object(urllib2, 'urlopen', Mock(return_value=urlopen_response))
    @patch.object(Setup, 'getAbsolutePath', new=mocked_getAbsolutePath)
    def test_metabans_plugin(self):
        global fake_download_url
        os.mkdir(os.path.join(tmp_dir, 'conf'))

        # create class instance to test
        setup = Setup()
        setup._set_external_dir = tmp_dir
        # call the method under test
        setup.download("metabans", fake_download_url, "metabans.zip")

        # verify that the work was done as intended
        plugin_module_dest_dir = os.path.join(tmp_dir, 'metabans')
        self.assertTrue(os.path.isdir(plugin_module_dest_dir), plugin_module_dest_dir)
        def assertIsFile(file):
            self.assertTrue(os.path.isfile(file), file + ' is not a file')
        assertIsFile(plugin_module_dest_dir + '/__init__.py')
        assertIsFile(plugin_module_dest_dir + '/somefile.py')
        assertIsFile(tmp_dir + '/conf/plugin_metabans.xml')
