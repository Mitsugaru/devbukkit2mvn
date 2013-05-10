devbukkit2mvn
=============

Python script for parsing plugins from DevBukkit, downloading binaries, and exporting them to a maven repository.

Uses [Bukget API v3](http://bukget.org/pages/docs/API3.html).

Dependencies
----

* [PyYAML](http://pyyaml.org/)

Usage
----

Simply run the export.py after configuring the config.yml.

Configuration
----

#### release
Defines the version to download, as defined by Bukget.

```
latest: Returns only the most current version.
release: Returns only the latest version tagged as a Stable release.
beta: Returns only the latest version tagged as a Beta release.
alpha: Returns only the latest version tagged as a Alpha release.
```

#### repository
Define the maven repository to deploy the artifacts to.

```
id: The identifier for the repository. Use in conjunction with the settings.xml to provide credentials.
url: Web URL for the maven repository.
```

#### main_class_length
Since this uses maven to generate a pom.xml stub with the essential identifiers for the artifact, the group id is defined by the plugin's main class. In order to group plugins with the same id, the main class is concatenated by the number given to this property.
By default, it is set to 3. So, a plugin with the main class:
```
com.github.user.someplugin.SomePlugin
```
Will have the group id of ```com.github.user```.

For plugins with shorter main class identifiers, such as ```src.ASDF```, it will just use whatever is available.

A group id must exist, thus you cannot set this parameter to zero or a negative value. In that case, it will use the default value.

Ideally, it would be nice to specify this per plugin since this value is not a "one size fits all" deal.

#### plugins
This is a list of plugin names / stubs (if you happen to know the Bukget stub identifier for a plugin). Case does not matter.
