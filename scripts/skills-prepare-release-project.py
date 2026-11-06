#!/usr/bin/env python3
"""Apply the reviewed public-build changes without depending on PBX object order."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess


def decode(text):
    return json.loads(subprocess.check_output(
        ['plutil', '-convert', 'json', '-o', '-', '-'], input=text.encode()))


def prepare(text):
    original = decode(text)
    expected = copy.deepcopy(original)
    objects = expected['objects']
    packages = {key for key, value in objects.items()
                if value.get('isa') == 'XCRemoteSwiftPackageReference'
                and value.get('repositoryURL', '').endswith('/native-apps-ducksans.git')}
    products = {key for key, value in objects.items()
                if value.get('isa') == 'XCSwiftPackageProductDependency'
                and value.get('productName') == 'DuckSansFont'}
    builds = {key for key, value in objects.items()
              if value.get('isa') == 'PBXBuildFile' and value.get('productRef') in products}
    if (len(packages), len(products), len(builds)) != (1, 1, 1):
        raise ValueError('Unexpected private font graph; review this upstream release')
    removed = packages | products | builds
    for key in removed:
        # Remove exact objects and array references; preserve upstream formatting.
        pattern = rf'^\t\t{key} /\*[^\n]*\*/ = (?:\{{[^\n]+\}};\n|\{{\n.*?^\t\t\}};\n)'
        text, count = re.subn(pattern, '', text, flags=re.MULTILINE | re.DOTALL)
        if count != 1:
            raise ValueError('Could not locate the exact private font object ' + key)
        text = re.sub(rf'^\t+{key} /\*[^\n]*\*/,\n', '', text, flags=re.MULTILINE)
        del objects[key]
    for value in objects.values():
        for key, field in value.items():
            if isinstance(field, list):
                value[key] = [entry for entry in field if not isinstance(entry, str) or entry not in removed]

    suffixes = {'com.duckduckgo.mobile.ios.CredentialExtension': 'CredentialExtension',
                'com.duckduckgo.mobile.ios.NetworkExtension': 'NetworkExtension'}
    changed = []
    for key, value in objects.items():
        settings = value.get('buildSettings', {})
        bundle = settings.get('PRODUCT_BUNDLE_IDENTIFIER')
        if value.get('isa') != 'XCBuildConfiguration' or value.get('name') != 'Debug' or bundle not in suffixes:
            continue
        sdk_key = 'PRODUCT_BUNDLE_IDENTIFIER[sdk=iphonesimulator*]'
        replacement = '$(APP_ID).' + suffixes[bundle]
        if sdk_key in settings:
            raise ValueError('Upstream already supplies a Simulator override; review it explicitly')
        pattern = rf'(^\t\t{key} /\*[^\n]*\*/ = \{{\n.*?^\t\t\}};)'
        blocks = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
        if len(blocks) != 1:
            raise ValueError('Could not locate the exact Debug configuration ' + key)
        block = blocks[0]
        old = '\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = ' + bundle + ';\n'
        new = old + '\t\t\t\t"' + sdk_key + '" = "' + replacement + '";\n'
        if block.group().count(old) != 1:
            raise ValueError('Unexpected extension bundle setting')
        text = text[:block.start()] + block.group().replace(old, new) + text[block.end():]
        settings[sdk_key] = replacement
        changed.append(key)
    if len(changed) != 2 or len(set(changed)) != 2:
        raise ValueError('Expected exactly two Debug extension configurations')
    if decode(text) != expected:
        raise ValueError('Project changed beyond the reviewed font and Simulator settings')
    return text, dict(removed_font_objects=sorted(removed), debug_configurations=changed,
                      before_sha256=hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest(),
                      after_sha256=hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest())


if __name__ == '__main__':
    project = Path('iOS/DuckDuckGo-iOS.xcodeproj/project.pbxproj')
    prepared, receipt = prepare(project.read_text())
    project.write_text(prepared)
    output = Path('release-input/project-preparation.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('Verified public-font removal and two Debug Simulator overrides; other project settings preserved.')
