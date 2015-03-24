Translator Plugin for BigBrotherBot
===================================

Description
-----------

A [BigBrotherBot][B3] plugin which is capable o translating in-game chat messages into a specified language.


Microsoft Translator API configuration
--------------------------------------

1. Create a new [Windows Live ID](https://signup.live.com)
2. Create an account on the [Azure Data Market](https://datamarket.azure.com/developer/applications/)
3. Pick a service [plan](https://datamarket.azure.com/dataset/1899a118-d202-492c-aa16-ba21c33c06cb)
4. Register an Azure [application](https://datamarket.azure.com/developer/applications)
5. While registering the new application you will need to specify a **website** and a **software name**: you can use
as website **http://localhost** and as software name whatever name you like more

The Azure Application registration, provides two critical fields for **API** access: **client id** and **client secret**:
you have to put those credentials inside the plugin configuration file.

In-game user guide
------------------

* **!translate [&lt;source&gt;]*[&lt;target&gt;] &lt;message&gt;** `translate a message`
* **!translast [&lt;target&gt;]** `translate the last available sentence from the chat`
* **!transauto &lt;on|off&gt;** `turn on/off the automatic translation`
* **!translang** `display the list of available language codes`