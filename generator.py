#!/usr/bin/env python

import sys, re, os, yaml, boto, xmltodict, argparse, urllib2

def main():
  parser = argparse.ArgumentParser(description = 'Sets S3 bucket redirect policy to defined values from config file')
  parser.add_argument('config_file', help = 'YAML configuration file', type = str, nargs = 1)
  parser.add_argument('-c', '--check', help = 'Check redirects after setting them', action = 'store_true')
  args = parser.parse_args()

  config = yaml.load(open(args.config_file[0], 'r'))

  s3connection = boto.connect_s3(config['iam_key'], config['iam_secret'])
  s3bucket = s3connection.get_bucket(config['bucket'])

  try:
    bucket_config = xmltodict.parse(s3bucket.get_website_configuration_with_xml()[1])
  except boto.exception.S3ResponseError:
    print 'The bucket "%s" is not a S3-website.' % config['bucket']
    sys.exit(1)

  suffix = bucket_config.get('WebsiteConfiguration').get('IndexDocument').get('Suffix')
  if bucket_config.get('WebsiteConfiguration').get('ErrorDocument'):
    error_key = bucket_config.get('WebsiteConfiguration').get('ErrorDocument').get('Key')
  else:
    error_key = None
  rules = boto.s3.website.RoutingRules()

  for key, target in config['redirects'].iteritems():
    url = re.search(r'(https?)://([^/]+)/?(.*)$', target.strip())
    rules.add_rule(boto.s3.website.RoutingRule
      .when(key_prefix = key)
      .then_redirect(hostname = url.group(2), protocol = url.group(1), replace_key = url.group(3))
    )

  if s3bucket.configure_website(suffix = suffix, error_key = error_key, routing_rules = rules):
    print 'Configuration for bucket "%s" set successful.' % config['bucket']

    if args.check:
      print 'Checking redirects...'
      for key, target in config['redirects'].iteritems():
        url = 'http://%s/%s' % (config['bucket'], key)
        if check_location_header(url, target):
          print '%s: OK' % key
        else:
          print '%s: ERR' % key

    sys.exit(0)
  else:
    print 'An error occured while configuring bucket "%s".' % config['bucket']
    sys.exit(1)

def check_location_header(url, expected):
  try:
    import httplib2
    h = httplib2.Http()
    h.follow_redirects = False
    (response, body) = h.request(url)
    return response['location'] == expected
  except httplib2.ServerNotFoundError, e:
    print 'An error occured while checking "%s"' % url
    print (e.message)
    sys.exit(1)

class HeadRequest(urllib2.Request):
  def get_method(self):
    return 'HEAD'

if __name__ == '__main__':
  main()
