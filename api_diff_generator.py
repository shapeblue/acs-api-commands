import xml.etree.ElementTree as ET
import argparse
import json
import os
from collections import defaultdict

def parse_commands(xml_file, version_filters=None, old_xml_file=None):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    commands = {}
    added_commands = []
    
    # Parse old version if provided
    old_commands = {}
    if old_xml_file:
        old_tree = ET.parse(old_xml_file)
        old_root = old_tree.getroot()
        for cmd in old_root.findall('command'):
            name = cmd.find('name').text
            req_args = {}
            req = cmd.find('request')
            if req is not None:
                for arg in req.findall('arg'):
                    arg_name = arg.find('name').text
                    required = arg.find('required').text.lower() == 'true'
                    req_args[arg_name] = required
            old_commands[name] = {'request': req_args}

    for cmd in root.findall('command'):
        name = cmd.find('name').text
        desc = cmd.find('description').text
        since = cmd.find('sinceVersion')
        if since is not None and since.text in version_filters:
            added_commands.append((name, desc))
        
        # Get all request parameters
        req_args = {}
        req = cmd.find('request')
        if req is not None:
            for arg in req.findall('arg'):
                arg_name = arg.find('name').text
                required = arg.find('required').text.lower() == 'true'
                req_args[arg_name] = required
        
        # Get all response parameters
        resp_args = set()
        resp = cmd.find('response')
        if resp is not None:
            for arg in resp.findall('arg'):
                arg_name = arg.find('name').text
                resp_args.add(arg_name)
        
        # Check for changed parameters
        changed_params = {}
        removed_params = []
        if old_xml_file and name in old_commands:
            old_req_args = old_commands[name]['request']
            # Check parameters that exist in both versions
            for arg_name, new_required in req_args.items():
                if arg_name in old_req_args and old_req_args[arg_name] != new_required:
                    changed_params[arg_name] = {
                        'required_old': old_req_args[arg_name],
                        'required_new': new_required
                    }
            # Check for removed parameters
            for arg_name in old_req_args:
                if arg_name not in req_args:
                    removed_params.append(arg_name)
        
        # Filter new parameters based on sinceVersion if filters are provided
        new_req_args = {}
        new_resp_args = set()
        if version_filters:
            req = cmd.find('request')
            if req is not None:
                for arg in req.findall('arg'):
                    arg_name = arg.find('name').text
                    since = arg.find('sinceVersion')
                    if since is not None and since.text in version_filters:
                        required = arg.find('required').text.lower() == 'true'
                        new_req_args[arg_name] = required
            resp = cmd.find('response')
            if resp is not None:
                for arg in resp.findall('arg'):
                    arg_name = arg.find('name').text
                    since = arg.find('sinceVersion')
                    if since is not None and since.text in version_filters:
                        new_resp_args.add(arg_name)
        else:
            new_req_args = req_args
            new_resp_args = resp_args
        
        commands[name] = {
            'request': new_req_args,
            'response': new_resp_args,
            'changed_params': changed_params,
            'removed_params': removed_params
        }
    return commands, added_commands

def main():
    parser = argparse.ArgumentParser(description='Extract new parameters and added commands from API XML files based on sinceVersion.')
    parser.add_argument('--xml', required=True, help='Path to the XML file to analyze (e.g., 4.20_commands.xml)')
    parser.add_argument('--old-xml', help='Path to the old version XML file for comparison (e.g., 4.19_commands.xml)')
    parser.add_argument('--output', required=True, help='Output file name (e.g., diff-4.20.1.txt)')
    parser.add_argument('--since', required=True, help='Comma-separated list of sinceVersion values to filter (e.g., 4.20.1,4.20.1.0)')
    parser.add_argument('--output-dir', help='Output directory (default: current directory)')
    args = parser.parse_args()

    version_filters = [v.strip() for v in args.since.split(',')]
    new_cmds, added_commands = parse_commands(args.xml, version_filters=version_filters, old_xml_file=args.old_xml)
    
    # Create output directory if specified
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_path = os.path.join(args.output_dir, args.output)
        json_path = os.path.join(args.output_dir, args.output.replace('.txt', '.json'))
    else:
        output_path = args.output
        json_path = args.output.replace('.txt', '.json')

    # Generate text file
    output = []
    if added_commands:
        output.append('Added commands:\n')
        for cmd, desc in sorted(added_commands):
            output.append(f'    {cmd} ({desc})\n\n')
    
    output.append('Changes in commands arguments:\n\n')
    for cmd in sorted(new_cmds.keys()):
        new_req_args = new_cmds[cmd]['request']
        new_resp_args = sorted(new_cmds[cmd]['response'])
        changed_params = new_cmds[cmd]['changed_params']
        removed_params = new_cmds[cmd]['removed_params']
        
        has_request_changes = new_req_args or changed_params or removed_params
        has_response_changes = new_resp_args
        
        if has_request_changes or has_response_changes:
            output.append(f'\t{cmd}\n\n')
            if has_request_changes:
                output.append(f'\t\tRequest:\n\n')
                if new_req_args:
                    req_params = [f"{arg} ({'required' if required else 'optional'})" for arg, required in sorted(new_req_args.items())]
                    output.append(f'\t\t\tNew parameters: {", ".join(req_params)}\n\n')
                if changed_params:
                    changed_params_list = [f"{arg} (old version - {'required' if info['required_old'] else 'optional'}, new version - {'required' if info['required_new'] else 'optional'})" 
                                         for arg, info in sorted(changed_params.items())]
                    output.append(f'\t\t\tChanged parameters: {", ".join(changed_params_list)}\n\n')
                if removed_params:
                    output.append(f'\t\t\tRemoved parameters: {", ".join(sorted(removed_params))}\n\n')
            if has_response_changes:
                output.append(f'\t\tResponse:\n\n')
                output.append(f'\t\t\tNew parameters: {", ".join(new_resp_args)}\n\n')

    with open(output_path, 'w') as f:
        f.writelines(output)

    # Generate JSON file
    json_output = {
        'commands_args_changed': [
            {
                'name': cmd,
                **({'request': {
                    'params_new': [{'name': arg, 'required': required} for arg, required in sorted(new_cmds[cmd]['request'].items())],
                    'params_changed': [{'name': arg, 'required_old': info['required_old'], 'required_new': info['required_new']} 
                                     for arg, info in sorted(new_cmds[cmd]['changed_params'].items())],
                    'params_removed': [{'name': arg} for arg in sorted(new_cmds[cmd]['removed_params'])]
                }} if (new_cmds[cmd]['request'] or new_cmds[cmd]['changed_params'] or new_cmds[cmd]['removed_params']) else {}),
                **({'response': {
                    'params_new': [{'name': arg} for arg in sorted(new_cmds[cmd]['response'])]
                }} if new_cmds[cmd]['response'] else {})
            }
            for cmd in sorted(new_cmds.keys())
            if new_cmds[cmd]['request'] or new_cmds[cmd]['response'] or new_cmds[cmd]['changed_params'] or new_cmds[cmd]['removed_params']
        ],
        'commands_added': [
            {'name': cmd, 'description': desc}
            for cmd, desc in sorted(added_commands)
        ],
        'commands_removed': [],
        'commands_sync_changed': []
    }

    with open(json_path, 'w') as f:
        json.dump(json_output, f, indent=2)

if __name__ == '__main__':
    main() 