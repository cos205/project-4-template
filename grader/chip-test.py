import os, shutil, sys, re, zipfile
import subprocess

from penalties import FormattedFeedback
from nand import hardware_simulator, assembler, cpu_emulator, vm_emulator, StudentProgram, \
                 file_generator, jack_compiler
import config
from chardet import detect
import secrets


def read_file(filename):
    with open(filename, 'rb') as f:
        try:
            bytes = f.read()
            return bytes.decode('utf-8').lower()
        except:
            d = detect(bytes)
            return bytes.decode(d['encoding']).lower()

def copy_folder(source, destination, permissions=None):
    shutil.copytree(source, destination, dirs_exist_ok=True)
    #if permissions:
    #    subprocess.run(['chmod', permissions, '-R', destination])


def find_subfolder(folder, file):
    """finds sub-folder which contains a file"""
    for root, f in file_generator(folder):
        if f.lower() == file.lower():
            return root
    return folder


def copy_upwards(folder, extension, correct=[]):
    """ copy files with specific extension from sub-folders upwards
        and fix upper/lower case mistakes """
    for root, f in file_generator(folder):
        if f.split('.')[-1].lower() == extension:
            try:
                #print(f'copying {os.path.join(root, f)} into {folder}')
                shutil.move(os.path.join(root, f), folder)
            except Exception as e:
                print('Exception occurred:')
                print(e)
                pass
            for c in correct:
                if f.lower() == c.lower() + extension and f != c + extension:
                    os.rename(os.path.join(folder, f), os.path.join(folder, c + extension))

def project_4(temp_dir, t):
    #print('temp_dir:', temp_dir)
    tests = ['Mult', 'Fill']
    copy_upwards(temp_dir, 'asm', tests)
    # Delete possible existing test files
    for root, f in file_generator(temp_dir):
        if f.lower().endswith('.tst') or f.lower().endswith('.cmp'):
            os.remove(os.path.join(root, f))
    copy_folder(os.path.join('grader/tests', 'p4'), temp_dir, permissions='a+rwx')
    feedback = FormattedFeedback(4)
    for test in [t]:
        filename = os.path.join(temp_dir, test)
        #print('checking file:', filename + '.asm')
        if not os.path.exists(filename + '.asm'):
            print(f'''File doen't exist:''', filename + '.asm')
            feedback.append(test, 'file_missing')
            continue
        output = assembler(temp_dir, test)
        if len(output) > 0:
            print('assembler error')
            feedback.append(test, 'assembly_error', output)
            continue
        output = cpu_emulator(temp_dir, test)
        if len(output) > 0:
            print('comparison error:', output)
            feedback.append(test, 'diff_with_test', output)
    return feedback.get()

# compare files ignoring whitespace
def compare_file(file1, file2):
    cmp_file = read_file(file1)
    xml_file = read_file(file2)
    return re.sub("\s*", "", cmp_file) == re.sub("\s*", "", xml_file)

def grader(filename, temp_dir, test):
    random_dir = 'temp-' + secrets.token_urlsafe(6)
    temp_dir = os.path.join(temp_dir, random_dir)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)
    os.mkdir(os.path.join(temp_dir, 'src'))
    shutil.copytree(filename, os.path.join(temp_dir,'src'), symlinks=False, ignore=None, ignore_dangling_symlinks=False, dirs_exist_ok=True)
    grade, feedback = project_4(temp_dir, test)
    #shutil.rmtree(temp_dir, ignore_errors=True)
    if feedback == '':
        feedback = 'Congratulations! all tests passed successfully!'
    return grade, feedback


def main():
    if len(sys.argv) < 3:
        print('Usage: python grader.py <dirname> <test>')
        print('For example: python grader.py project3 RAM')
    else:
        temp = os.path.join('grader','temp')
        if not os.path.exists(temp):
            os.mkdir(temp)
        grade, feedback = grader(sys.argv[1], temp , sys.argv[2])
        print(feedback)


if __name__ == '__main__':
    main()
