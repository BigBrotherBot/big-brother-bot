Miscellaneous
=============

Duration syntax
---------------

Many plugin settings need to express durations. For this purpose, B3 provides a convenient syntax using a suffix for
expressing different duration units :

s
  second *i.e.:* ``45s``
  
m
  minute *i.e.:* ``5m``
  
h
  hour *i.e.:* ``1h``
  
d 
  day *i.e.:* ``7d``

w
  week *i.e.:* ``4w``

For example, let's say you want to ban player Joe for 1 week with reason '*insult other players*', you would use the
command :

``!ban joe 1w insult other players``