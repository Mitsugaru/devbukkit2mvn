#Imports
import json
import urllib2
import re
import os
import errno
import yaml
import sys

# from http://stackoverflow.com/a/3382869
def require_dir(path):
    try:
        os.makedirs(path)
    except OSError, exc:
        if exc.errno != errno.EEXIST:
            raise

# http://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string
def findnth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

# Get the plugin details from the slug
def parse_plugin_details(slug, version):
  page = urllib2.urlopen("http://api.bukget.org/3/plugins/bukkit/" + slug + "/" + version)
  return json.load(page)

# Download the plugin jar from the given website and save it to the file
def download_plugin(filename, url_source):
  # Make sure filename is not empty
  if filename and not os.path.exists(filename):
    f = urllib2.urlopen(url_source)
    data = f.read()
    with open(filename, "wb") as code:
      code.write(data)

# Validate the given plugin item
def validate_plugin_item(item):
  valid = True
  if not "versions" in item:
    print "!!! No versions"
    valid = False
  elif not "main" in item:
    print "!!! missing main"
    valid = False
  return valid

# Export the file to maven repository
def export_to_maven(repo_url, repo_id, group_id, artifact_id, version, filename):
  command = "mvn deploy:deploy-file \
    -Durl=" + repo_url + " \
    -DrepositoryId=" + repo_id + " \
    -DgroupId=" + group_id + " \
    -DartifactId=" + artifact_id + " \
    -Dversion=" + version +"  \
    -Dpackaging=jar \
    -Dfile=\"" + os.path.abspath(filename) +"\""
  print command
  return os.system(command)

# Main class
class MainClass:

  # load configuration from config.yml
  def load_configuration(self):
    conf = yaml.load(open('config.yml'))
    repo_conf = conf.get("repository", "")
    if repo_conf:
      self.repository_id = repo_conf.get("id", self.repository_id)
      self.repository_url = repo_conf.get("url", self.repository_url)
    self.short_main_length = conf.get("main_class_length", self.short_main_length)
    plugin_list = conf.get("plugins", "")
    if plugin_list:
      for plugin in plugin_list:
        self.target_plugins.append(plugin.lower())
    self.release_flag = conf.get("release", self.release_flag).lower()

  # load default configuration
  def load_defaults(self):
    self.repository_id = "internal"
    self.repository_url = "UNKNOWN"
    self.short_main_length = 3
    self.target_plugins = []
    self.release_flag = "latest"

  def validate_configuration(self):
    #Check that the shortened length is not less than or equal to 0
    if self.short_main_length <= 0:
      self.short_main_length = 3

  # run function
  def run(self):
    # Get configuration options
    self.load_defaults()
    self.load_configuration()
    self.validate_configuration()
    
    if len(self.target_plugins) == 0:
      print "!!! No target plugins to download..."
      sys.exit()

    # Get the downloads directory
    # TODO configurable?
    downloads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
    require_dir(downloads_dir)

    # Using BukGet
    # API: http://bukget.org/pages/docs/API3.html

    #Get the plugin slugs and names
    slug_page = urllib2.urlopen("http://api.bukget.org/3/plugins/bukkit?fields=slug,plugin_name")
    slug_json = json.load(slug_page)

    # Iterate over the slugs
    for slug_item in slug_json:
      
      # Check if we're done
      if len(self.target_plugins) == 0:
        print "Done"
        break

      slug = slug_item["slug"]
      plugin_name = slug_item.get('plugin_name', "UNKNOWN")
      plugin_website = slug_item.get('webpage',"")
      
      # Check if this is a plugin we want
      found_slug = False
      found_name = False
      if plugin_name.lower() in self.target_plugins:
        self.target_plugins.remove(plugin_name.lower())
        found_name = True
      elif slug.lower() in self.target_plugins:
        self.target_plugins.remove(slug.lower())
        found_slug = True
        
      if not found_name and not found_slug:
        continue
        
      if found_slug:
        print "=== Attempting: " + slug
      elif found_name:
        print "=== Attempting: " + plugin_name

      #TODO from config, allow specifiers for latest, stable, beta, alpha versions
      #Use API to get these versions
      plugin_details = parse_plugin_details(slug, self.release_flag)

      # Validate plugin
      if validate_plugin_item(plugin_details):
        main_class_path = plugin_details["main"]
        short_cutoff = findnth(main_class_path, ".", self.short_main_length)
        short_main = main_class_path

        # Need to check in case of ridiculously short main class paths
        if short_cutoff > 0:
          short_main = main_class_path[:short_cutoff]
            
        # Grab version(s)
        for version_details in plugin_details["versions"]:
          download_link = version_details["download"]
          filename = version_details["filename"]
          version = version_details["version"]
            
          extension = os.path.splitext(filename)[1]
            
          if extension != "jar":
            print "Skipping " + plugin_name + " v" + version + " because it is not a jar..."
            continue
            
          print filename + " : " + version + " : " + download_link
          # download file
          download_plugin(filename, download_link)
          # export jar to maven
          export_to_maven(self.repository_url, self.repository_id, short_main, plugin_name, version, filename)
          # delete downloaded file
          os.remove(filename)
      else:
        if found_slug:
          self.target_plugins.append(slug.lower())
        elif found_name:
          self.target_plugins.append(plugin_name.lower())
        print "!!! Errors in validating '" + slug + "' | '" + plugin_name + "' @ " + plugin_website

    # Notify user of any plugins we could not download
    if len(self.target_plugins) != 0:
      print "!!! Could not find / export the following plugins: "
      for plugin in self.target_plugins:
        print " - " + plugin

# Main function
def main():
  mc = MainClass()
  mc.run()

if __name__ == "__main__":
    main()
