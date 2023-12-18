import os
import subprocess
import xml.etree.ElementTree as ET
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_dependency_version(root_directory, main_branch, dependency_name, new_version):
    for root, dirs, files in os.walk(root_directory):
        for file in files:
            if file == 'pom.xml' or file == 'build.gradle':
                project_dir = os.path.dirname(os.path.join(root, file))
                #run_git_command(f"git pull origin {main_branch}", project_dir)
                run_git_command("git checkout -b feature/autoVersioning", project_dir)

                full_path = os.path.join(root, file)
                if file == 'pom.xml':
                    update_pom_file(full_path, dependency_name, new_version)
                elif file == 'build.gradle':
                    update_gradle_file(full_path, dependency_name, new_version)

                # Add and commit the change
                if has_uncommitted_changes(project_dir):
                    run_git_command(f"git add {full_path}", project_dir)
                    message = f"Update {dependency_name} version to {new_version}'"
                    run_git_command(f"git commit -m '{message}'", project_dir)                 
                     #run_git_command("git push --set-upstream origin feature/autoVersioning", project_dir)
                else:
                    logging.info(f"No changes to commit in {project_dir}")
                # Push the new branch

    # Push the new branch
    # run_git_command("git push --set-upstream origin feature/autoVersioning", root_directory)

def update_pom_file(file_path, dependency_name, new_version):
    try:
        ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
        tree = ET.parse(file_path)
        root_element = tree.getroot()

        # Check for both version.<dependency> and <dependency>.version
        version_tags = [
            root_element.find(f'.//{{http://maven.apache.org/POM/4.0.0}}version.{dependency_name}'),
            root_element.find(f'.//{{http://maven.apache.org/POM/4.0.0}}{dependency_name}.version')
        ]

        for version_tag in version_tags:
            if version_tag is not None:
                version_tag.text = new_version
                tree.write(file_path, xml_declaration=True, encoding='utf-8')
                logging.info(f"Updated {dependency_name} version in {file_path} to {new_version}")
                break
    except ET.ParseError as e:
        logging.error(f"Error parsing {file_path}: {e}")

def update_gradle_file(file_path, dependency_name, new_version):
    try:
        with open(file_path, 'r') as file:
            content = file.read()

        # Adjust the regular expression to match the entire dependency line and replace only the version number
        pattern = re.compile(rf"(implementation\s+'[^']+:{dependency_name}:)[^']+'")
        content, count = pattern.subn(rf"\g<1>{new_version}'", content)

        if count > 0:
            with open(file_path, 'w') as file:
                file.write(content)
            logging.info(f"Updated {dependency_name} version in {file_path} to {new_version}")
    except IOError as e:
        logging.error(f"Error reading or writing to {file_path}: {e}")

def run_git_command(command, project_dir):
    try:
        # Split the command into a list of arguments
        command_list = command.split()

        # Special handling for 'commit -m' to keep the message intact
        if "commit" in command_list and "-m" in command_list:
            message_index = command_list.index("-m") + 1
            if message_index < len(command_list):
                commit_message = ' '.join(command_list[message_index:])
                command_list = command_list[:message_index] + [commit_message.strip("'")]

        subprocess.run(command_list, cwd=project_dir, shell=True, check=True, text=True)
        logging.info(f"Successfully ran git command: {command}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running git command '{command}' in '{project_dir}': {e}")
        if "checkout" in command and "Please commit your changes" in str(e):
            stash_name = f"auto-stash-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            logging.warning(f"Uncommitted changes detected. Stashing changes as '{stash_name}' before switching branches.")
            stash_command = f"git stash push -m {stash_name}"
            subprocess.run(stash_command, cwd=project_dir, check=True, shell=True)
            logging.info("Changes stashed successfully.")
            subprocess.run(command, cwd=project_dir, check=True, shell=True)  # Retry the original command
        else:
            logging.error(f"Error running git command '{command}': {e}")
def has_uncommitted_changes(project_dir):
    try:
        result = subprocess.run("git status --porcelain", cwd=project_dir, check=True, shell=True, stdout=subprocess.PIPE)
        return len(result.stdout) > 0
    except subprocess.CalledProcessError as e:
        logging.error(f"Error checking for uncommitted changes in '{project_dir}': {e}")
        return False

# Example usage
# root_directory = "C:\\Users\\IdeaProjects\\PIT"
# main_branch = "master"
# dependency_name = "spring-boot-starter"
# new_version = "7.7.7"

root_directory = input("Enter the root directory: ")
main_branch = input("Enter the main branch name, this can be Main, Master or Development: ")
dependency_name = input("Enter the Artifact Name: ")
new_version = input("Enter the new version: ")


cat_art = '''
 /\_/\  
( o.o ) > "Check the info and type 'yes' to proceed."
 > ^ <
'''

print("\nPlease double-check the provided information:")
print("Root Directory:", root_directory)
print("Main Branch:", main_branch)
print("Dependency Artifact Name:", dependency_name)
print("New Version:", new_version)
print(cat_art)

confirmation = input("Is the above information correct? (yes/no): ").lower()
if confirmation == 'yes':
    update_dependency_version(root_directory, main_branch, dependency_name, new_version)
else:
    print("Operation cancelled. Please rerun the script with correct information.")
