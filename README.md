acs-api-commands
================

Collection of API commands.xml of [Apache CloudStack](http://cloudstack.apache.org/) versions. used to generate
[Apache CloudStack Release Notes](http://docs.cloudstack.apache.org/en/latest/releasenotes/index.html).

[How To Generate CloudStack API Documentation](https://cwiki.apache.org/confluence/display/CLOUDSTACK/How+To+Generate+CloudStack+API+Documentation)


Install NonOSS Dependencies
---------------------------

```bash
$ cd /tmp
$ git clone https://github.com/rhtyd/cloudstack-nonoss.git nonoss
$ cd nonoss && bash -x install-non-oss.sh
```

Build API doc
-------------

```bash
$ cd /path/to/cloudstack
$ git fetch <upstream>
$ git checkout main
$ git checkout <release_commit>
$ mvn -Pdeveloper -Dnoredist clean install -DskipTests=true
$ mvn -Pdeveloper -Dnoredist clean install -pl :cloud-apidoc
```

Generate Diff - for Major releases
-------------

```bash
$ cd /path/to/cloudstack
$ export COMMANDS=/path/to/acs-api-commands
$ export OLD_RELEASE=4.13
$ export NEW_RELEASE=4.14
$ cp tools/apidoc/target/commands.xml $COMMANDS/${NEW_RELEASE}_commands.xml
$ mkdir $COMMANDS/diff-${OLD_RELEASE//.}-${NEW_RELEASE//.}
$ java -cp $HOME/.m2/repository/com/thoughtworks/xstream/xstream/1.4.11.1/xstream-1.4.11.1.jar:$HOME/.m2/repository/com/google/code/gson/gson/1.7.2/gson-1.7.2.jar:server/target/classes com.cloud.api.doc.ApiXmlDocReader -old $COMMANDS/${OLD_RELEASE}_commands.xml -new $COMMANDS/${NEW_RELEASE}_commands.xml -d $COMMANDS/diff-${OLD_RELEASE//.}-${NEW_RELEASE//.}
```

Note
----

- For easier automation (i.e. select the "OLD_RELEASE" by simply choosing a previous branch like "4.12" or 4.13")
- and
- taking into consideration that the minor release never has a new/removed API/command (and very rarely changed/updated an existing API call)
- and
- taking into the consideration that we have never so far documented API changes between minor versions (i.e. 4.11.0 and 4.11.1), 
- ...
- the naming scheme, used as of 4.11, is now in X.Y form (i.e. 4.11 or 4.12) instead of minor version (4.11.0 or 4.12.0), 
while the older generated documentation was moved to folder "before-4.11".

In order to generate .rst version based on the diffs generated here, as well as for the generating a list of PRs/changes/fixed issues in the new release, please see https://github.com/swill/generate_acs_rn 



Generate the diff for Minor releases (and experimental for major releases):

Run the automation script `api_diff_generator` 

# API Diff Generator

This script analyzes API XML files to identify changes between versions, including new commands, parameter changes, and removed parameters.

## Usage

```bash
python3 api_diff_generator.py --xml <new_xml_file> --old-xml <old_xml_file> --output <output_file> --since <version> [--output-dir <directory>]
```

## Parameters

- `--xml` (required): Path to the new version XML file to analyze (e.g., `4.20_commands.xml`)
- `--old-xml`: Path to the old version XML file for comparison (e.g., `4.19_commands.xml`). If provided, the script will identify:
  - Changed parameters (where required/optional status changed)
  - Removed parameters
- `--output` (required): Output file name (e.g., `diff-4.20.1.txt`). The script will generate:
  - A text file with the specified name
  - A JSON file with the same name but `.json` extension
- `--since`: Comma-separated list of version numbers to filter changes (e.g., `4.20.1,4.20.1.0`). Only changes with matching `sinceVersion` will be included
- `--output-dir`: Output directory for the generated files (default: current directory)

## Output Format

### Text File
The text file will show:
1. Added commands (with descriptions)
2. Changes in command arguments:
   - New parameters (with required/optional status)
   - Changed parameters (showing old and new required/optional status)
   - Removed parameters
   - New response parameters

### JSON File
The JSON file will contain:
```json
{
  "commands_args_changed": [
    {
      "name": "commandName",
      "request": {
        "params_new": [{"name": "param", "required": true/false}],
        "params_changed": [{"name": "param", "required_old": true/false, "required_new": true/false}],
        "params_removed": [{"name": "param"}]
      },
      "response": {
        "params_new": [{"name": "param"}]
      }
    }
  ],
  "commands_added": [
    {"name": "commandName", "description": "command description"}
  ],
  "commands_removed": [],
  "commands_sync_changed": []
}
```

## Example

```bash
python3 api_diff_generator.py --xml 4.20_commands.xml --old-xml 4.19_commands.xml --output diff-4.20.1.txt --since 4.20.1,4.20.1.0 --output-dir diff-419-420
```

This will:
1. Compare `4.20_commands.xml` with `4.19_commands.xml`
2. Filter changes for version 4.20.1
3. Generate output files in the `diff-419-420` directory:
   - `diff-4.20.1.txt`
   - `diff-4.20.1.json`
