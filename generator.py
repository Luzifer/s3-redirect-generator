#!/usr/bin/env python

import sys, re, os
import xml.etree.cElementTree as ET

if len(sys.argv) != 2:
  print 'Usage: %s <redirects file>' % os.path.basename(sys.argv[0])
  sys.exit(1)

root = ET.Element('RoutingRules')

try:
  infile = open(sys.argv[1], 'r')
except IOError:
  print 'Redirects file has not been found or is not readable.'
  sys.exit(2)

for line in infile:
  parts = line.split(' = ')
  rule = ET.SubElement(root, 'RoutingRule')

  condition = ET.SubElement(rule, 'Condition')
  ET.SubElement(condition, 'KeyPrefixEquals').text = parts[0].strip()

  url = re.search(r'(https?)://([^/]+)/?(.*)$', parts[1].strip())

  redirect = ET.SubElement(rule, 'Redirect')
  ET.SubElement(redirect, 'Protocol').text = url.group(1)
  ET.SubElement(redirect, 'HostName').text = url.group(2)
  ET.SubElement(redirect, 'ReplaceKeyWith').text = url.group(3)
  ET.SubElement(redirect, 'HttpRedirectCode').text = '302'

tree = ET.ElementTree(root)
tree.write(sys.stdout)

print
