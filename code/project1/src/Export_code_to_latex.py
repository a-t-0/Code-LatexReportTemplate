# runs a jupyter notebook and converts it to pdf
import os
import shutil
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def export_code_to_latex(main_latex_filename, project_nr):
    """This function exports the python files and compiled pdfs of jupiter notebooks into the 
    latex of the same project number. First it scans which appendices (without code, without 
    notebooks) are already manually included in the main latex code. Next, all appendices
    that contain the python code are eiter found or created in the following order:
    First, the __main__.py file is included, followed by the main.py file, followed by all
    python code files in alphabetic order. After this, all the pdfs of the compiled notebooks
    are added in alphabetic order of filename. This order of appendices is overwritten in the
    main tex file.
    
    :param main_latex_filename: Name of the main latex document of this project number
    :param project_nr: The number  indicating which project this code pertains to.
    """
    script_dir = get_script_dir()
    relative_dir = f'latex/project{project_nr}/'
    appendix_dir = script_dir+'/../../../'+relative_dir+'Appendices/'
    path_to_main_latex_file = f'{script_dir}/../../../{relative_dir}/{main_latex_filename}'
    root_dir = script_dir[0:script_dir.rfind(f'code/project{project_nr}')]
    
    python_filepaths = get_filenames_in_dir('py',script_dir, ['__init__.py'])
    compiled_notebook_pdf_filepaths = get_compiled_notebook_paths(script_dir)
    
    python_files_already_included_in_appendices = get_code_files_already_included_in_appendices(python_filepaths, appendix_dir, '.py', project_nr, root_dir)
    notebook_pdf_files_already_included_in_appendices = get_code_files_already_included_in_appendices(compiled_notebook_pdf_filepaths, appendix_dir, '.ipynb', project_nr, root_dir)
    
    missing_python_files_in_appendices = get_code_files_not_yet_included_in_appendices(python_filepaths, python_files_already_included_in_appendices, '.py')
    missing_notebook_files_in_appendices = get_code_files_not_yet_included_in_appendices(compiled_notebook_pdf_filepaths, notebook_pdf_files_already_included_in_appendices, '.pdf')
    
    created_python_appendix_filenames = create_appendices_with_code(appendix_dir, missing_python_files_in_appendices, '.py',  project_nr, root_dir)
    created_notebook_appendix_filenames = create_appendices_with_code(appendix_dir, missing_notebook_files_in_appendices, '.ipynb', project_nr, root_dir)
    
    appendices = get_list_of_appendix_files(appendix_dir, compiled_notebook_pdf_filepaths, python_filepaths)
    
    main_tex_code, start_index, end_index, appendix_tex_code = get_appendix_tex_code(path_to_main_latex_file)
    # assumes non-included non-code appendices should not be included:
    non_code_appendices, main_non_code_appendix_inclusion_lines = get_order_of_non_code_appendices_in_main(appendices, appendix_tex_code) 
    
    python_appendix_filenames = list(map(lambda x: x.appendix_filename, filter_appendices_by_type(appendices, 'python')))
    sorted_created_python_appendices = sort_python_appendices(filter_appendices_by_type(appendices, 'python'))
    sorted_python_appendix_filenames = list(map(lambda x: x.appendix_filename, sorted_created_python_appendices))
    
    notebook_appendix_filenames = list(map(lambda x: x.appendix_filename, filter_appendices_by_type(appendices, 'notebook')))
    sorted_created_notebook_appendices = sort_notebook_appendices_alphabetically(filter_appendices_by_type(appendices, 'notebook'))
    sorted_notebook_appendix_filenames = list(map(lambda x: x.appendix_filename, sorted_created_notebook_appendices))
    
    appendix_latex_code = create_appendices_latex_code(main_non_code_appendix_inclusion_lines,  sorted_created_notebook_appendices, project_nr, sorted_created_python_appendices)
    
    updated_main_tex_code = substitute_appendix_code(end_index, main_tex_code, start_index, appendix_latex_code)
    
    overwrite_content_to_file(updated_main_tex_code, path_to_main_latex_file)
    
    
def create_appendices_latex_code(main_non_code_appendix_inclusion_lines, notebook_appendices, project_nr, python_appendices):
    """Creates the latex code that includeds the appendices in the main latex file.

    :param main_non_code_appendix_inclusion_lines: latex code that includes the appendices that do not contain python code nor notebooks
    :param notebook_appendices: List of Appendix objects representing appendices that include the pdf files of compiled Jupiter notebooks
    :param project_nr: The number indicating which project this code pertains to. 
    :param python_appendices: List of Appendix objects representing appendices that include the python code files.
    """
    main_appendix_inclusion_lines = main_non_code_appendix_inclusion_lines
    for appendix in python_appendices:
        line = update_appendix_tex_code(appendix.appendix_filename, project_nr)
        main_appendix_inclusion_lines.append(line)
    
    for appendix in notebook_appendices:
        line = update_appendix_tex_code(appendix.appendix_filename, project_nr)
        main_appendix_inclusion_lines.append(line)
    return main_appendix_inclusion_lines
        
        
def filter_appendices_by_type(appendices, appendix_type):
    """Returns the list of all appendices of a certain appendix type, from the incoming list of Appendix objects.

    :param appendices: List of Appendix objects
    :param appendix_type: Can consist of "no_code", "python", or "notebook" and indicates different appendix types
    """
    return_appendices = []
    for appendix in appendices:
        if appendix.appendix_type == appendix_type:
            return_appendices.append(appendix)
    return return_appendices
    
    
def sort_python_appendices(appendices):
    """First puts __main__.py, followed by main.py followed by a-z code files.

    :param appendices: List of Appendix objects
    """
    return_appendices = []
    for appendix in appendices: # first get appendix containing __main__.py
        if (appendix.code_filename=="__main__.py") or (appendix.code_filename=="__Main__.py"):
            return_appendices.append(appendix)
            appendices.remove(appendix)
    for appendix in appendices: # second get appendix containing main.py
        if (appendix.code_filename=="main.py") or (appendix.code_filename=="Main.py"):
            return_appendices.append(appendix)
            appendices.remove(appendix)
    return_appendices
    
    # Filter remaining appendices in order of a-z
    filtered_remaining_appendices = [i for i in appendices if i.code_filename is not None]
    appendices_sorted_a_z = sort_appendices_on_code_filename(filtered_remaining_appendices)
    return return_appendices+appendices_sorted_a_z
    

def sort_notebook_appendices_alphabetically(appendices):
    """Sorts notebook appendix objects alphabetic order of their pdf filenames.

    :param appendices: List of Appendix objects
    '"""
    return_appendices = []
    filtered_remaining_appendices = [i for i in appendices if i.code_filename is not None]
    appendices_sorted_a_z = sort_appendices_on_code_filename(filtered_remaining_appendices)
    return return_appendices+appendices_sorted_a_z
    
    
def sort_appendices_on_code_filename(appendices):
    """Returns a list of Appendix objects that are sorted and  based on the property: code_filename.
    Assumes the incoming appendices only contain python files.

    :param appendices: List of Appendix objects 
    """
    attributes = list(map(lambda x: x.code_filename, appendices))
    sorted_indices = sorted(range(len(attributes)), key=lambda k: attributes[k])
    sorted_list = []
    for i in sorted_indices:
        sorted_list.append(appendices[i])
    return sorted_list
            
            
def get_order_of_non_code_appendices_in_main(appendices, appendix_tex_code):
    """Scans the lines of appendices in the main code, and returns the lines
    of the appendices that do not contain code, in the order in which they were 
    included in the main latex file.

    :param appendices: List of Appendix objects 
    :param appendix_tex_code: latex code from the main latex file that includes the appendices
    """
    non_code_appendices = []
    non_code_appendix_lines = []
    appendix_tex_code = list(dict.fromkeys(appendix_tex_code))
    for line in appendix_tex_code:
        appendix_filename = get_filename_from_latex_appendix_line(appendices, line)
        
        # Check if line is not commented
        if not appendix_filename is None:
            if not line_is_commented(line,appendix_filename):
                appendix = get_appendix_from_filename(appendices, appendix_filename)
                if appendix.appendix_type == "no_code":
                    non_code_appendices.append(appendix)
                    non_code_appendix_lines.append(line)
    return non_code_appendices, non_code_appendix_lines


def get_filename_from_latex_appendix_line(appendices, appendix_line):
    """Returns the first filename from a list of incoming filenames that 
    occurs in a latex code line.

    :param appendices: List of Appendix objects 
    :param appendix_line: latex code (in particular expected to be the code from main that is used to include appendix latex files.)
    """
    for filename in list(map(lambda appendix: appendix.appendix_filename, appendices)):
        if filename in appendix_line:
            if not line_is_commented(appendix_line, filename):
                return filename
            
            
def get_appendix_from_filename(appendices, appendix_filename):
    """Returns the first Appendix object with an appendix filename that matches the incoming appendix_filename.
    The Appendix objects are selected from an incoming list of Appendix objects.

    :param appendices: List of Appendix objects 
    :param appendix_filename: name of a latex appendix file, ends in .tex,
    """
    for appendix in appendices:
        if appendix_filename == appendix.appendix_filename:
            return appendix
            
            
def get_compiled_notebook_paths(script_dir):
    """Returns the list of jupiter notebook filepaths that were compiled successfully and that are
    included in the same dias this script (the src directory).

    :param script_dir: absolute path of this file.
    """
    notebook_filepaths= get_filenames_in_dir('.ipynb', script_dir)
    compiled_notebook_filepaths = []
    
    # check if the jupyter notebooks were compiled
    for notebook_filepath in notebook_filepaths:
        
        # swap file extension
        notebook_filepath = notebook_filepath.replace('.ipynb','.pdf')
        
        # check if file exists
        if os.path.isfile(notebook_filepath):
            compiled_notebook_filepaths.append(notebook_filepath)
    return compiled_notebook_filepaths
    
    
def get_list_of_appendix_files(appendix_dir, absolute_notebook_filepaths, absolute_python_filepaths):
    """Returns a list of Appendix objects that contain all the appendix files with .tex extension.

    :param appendix_dir: Absolute path that contains the appendix .tex files.
    :param absolute_notebook_filepaths: List of absolute paths to the compiled notebook pdf files.
    :param absolute_python_filepaths: List of absolute paths to the python files.
    """
    appendices = []
    appendices_paths = get_filenames_in_dir('.tex', appendix_dir)
    
    for appendix_filepath in appendices_paths:
        appendix_type = "no_code"
        appendix_filecontent = read_file(appendix_filepath)
        line_nr_python_file_inclusion = get_line_of_latex_command(appendix_filecontent, "\pythonexternal{")
        line_nr_notebook_file_inclusion = get_line_of_latex_command(appendix_filecontent, "\includepdf[pages=")
        if  line_nr_python_file_inclusion > -1:
            appendix_type = "python"
            # get python filename
            line = appendix_filecontent[line_nr_python_file_inclusion]
            filename = get_filename_from_latex_inclusion_command(line, '.py', "\pythonexternal{")
            appendices.append(Appendix(appendix_filepath, appendix_filecontent, appendix_type, filename, line))
        if line_nr_notebook_file_inclusion > -1:
            appendix_type = "notebook"
            line = appendix_filecontent[line_nr_notebook_file_inclusion]
            filename = get_filename_from_latex_inclusion_command( line, '.pdf', "\includepdf[pages=")
            appendices.append(Appendix(appendix_filepath, appendix_filecontent, appendix_type, filename, line))
        else:
            appendices.append(Appendix(appendix_filepath, appendix_filecontent, appendix_type))
    return appendices
    
    
def get_filename_from_latex_inclusion_command(appendix_line, extension, start_substring):
    """returns the code/notebook filename in a latex command which includes that code in an appendix.
    The inclusion command includes a python code or jupiter notebook pdf.

    :param appendix_line: :Line of latex code (in particular expected to be the latex code from an appendix.).
    :param extension: The file extension of the file that is sought in the appendix line. Either ".py" or ".pdf".
    :param start_substring: The substring that characterises the latex inclusion command.
    """
    start_index = appendix_line.index(start_substring)
    end_index = appendix_line.index(extension)
    return get_filename_from_dir(appendix_line[start_index:end_index+len(extension)])

    
def get_filenames_in_dir(extension, path, excluded_files=None):
    """Returns a list of the relative paths to all files within the some path that match
    the given file extension.

    :param extension: The file extension of the file that is sought in the appendix line. Either ".py" or ".pdf".
    :param path: Absolute filepath in which files are being sought.
    :param excluded_files: (Default value = None) Files that will not be included even if they are found.
    """
    filepaths=[]
    for r, d, f in os.walk(path):
        for file in f:
            if file.endswith(extension):
                if (excluded_files is None) or ((not excluded_files is None) and (not file in excluded_files)):
                    filepaths.append(r+'/'+file)
    return filepaths
    
    
def get_code_files_already_included_in_appendices(absolute_code_filepaths, appendix_dir, extension, project_nr, root_dir):
    """Returns a list of code filepaths that are already properly included the latex appendix files of this project.

    :param absolute_code_filepaths: List of absolute paths to the code files (either python files or compiled jupyter notebook pdfs).
    :param appendix_dir: Absolute path that contains the appendix .tex files.
    :param extension: The file extension of the file that is sought in the appendix line. Either ".py" or ".pdf". 
    :param project_nr: The number  indicating which project this code pertains to. 
    :param root_dir: The root directory of this repository.
    """
    appendix_files = get_filenames_in_dir('.tex', appendix_dir)
    contained_codes = []
    for code_filepath in absolute_code_filepaths:
        for appendix_filepath in appendix_files:
            appendix_filecontent = read_file(appendix_filepath)
            line_nr = check_if_appendix_contains_file(appendix_filecontent, code_filepath, extension, project_nr, root_dir)
            if line_nr>-1:
                # add filepath to list of files that are already in the appendices
                contained_codes.append(Appendix_with_code(code_filepath,
                appendix_filepath,
                appendix_filecontent,
                line_nr, 
                '.py'))
    return contained_codes
    
    
def check_if_appendix_contains_file(appendix_content, code_filepath, extension, project_nr, root_dir):
    """Scans an appendix content to determine whether it contains a substring that
    includes a code file (of either python or compiled notebook=pdf extension).

    :param appendix_content: content in an appendix latex file.
    :param code_filepath: Absolute path to a code file (either python files or compiled jupyter notebook pdfs).
    :param extension: The file extension of the file that is sought in the appendix line. Either ".py" or ".pdf". 
    :param project_nr: The number  indicating which project this code pertains to. 
    :param root_dir: The root directory of this repository. 
    """
    # convert code_filepath to the inclusion format in latex format
    latex_relative_filepath = f'latex/project{project_nr}/../../{code_filepath[len(root_dir):]}'
    latex_command = get_latex_inclusion_command(extension, latex_relative_filepath)
    return get_line_of_latex_command(appendix_content, latex_command)
    
    
def get_line_of_latex_command(appendix_content, latex_command):
    """Returns the line number of a latex command if it is found. Returns -1 otherwise.

    :param appendix_content: content in an appendix latex file.
    :param latex_command: A line of latex code. (Expected to come from some appendix)
    """
    # check if the file is in the latex code
    line_nr = 0
    for line in appendix_content:
        if latex_command in line:
            if line_is_commented(line,latex_command):
                commented=True
            else:
                return line_nr
        line_nr=line_nr+1
    return -1
    
    
def line_is_commented(line, target_substring):
    """Returns True if a latex code line is commented, returns False otherwise

    :param line: A line of latex code that contains a relevant command (target substring).
    :param target_substring: Used to determine whether the command that is found is commented or not.
    """
    left_of_command = line[:line.rfind(target_substring)]
    if '%' in left_of_command:
        return True
    return False
                
    
def get_latex_inclusion_command(extension, latex_relative_filepath_to_codefile):
    """Creates and returns a latex command that includes either a python file or a compiled jupiter 
    notebook pdf (whereever the command is placed). The command is intended to be placed in the appendix.

    :param extension: The file extension of the file that is sought in the appendix line. Either ".py" or ".pdf". 
    :param latex_relative_filepath_to_codefile: The latex compilation requires a relative path towards code files
    that are included. Therefore, a relative path towards the code is given.

    """
    if extension==".py":
        left = "\pythonexternal{"
        right = "}"
        latex_command = f'{left}{latex_relative_filepath_to_codefile}{right}'
    elif extension==".ipynb":
        
        left = "\includepdf[pages=-]{"
        right = "}"
        latex_command = f'{left}{latex_relative_filepath_to_codefile}{right}'
    return latex_command
    
    
def read_file(filepath):
    """Reads content of a file and returns it as a list of strings

    :param filepath: 

    """
    with open(filepath) as f:
        content = f.readlines()
    return content  


def get_code_files_not_yet_included_in_appendices(code_filepaths, contained_codes, extension):
    """Returns a list of filepaths that are not yet properly included in some appendix of this projectX,

    :param code_filepaths: 
    :param contained_codes: 
    :param extension: The file extension of the file that is sought in the appendix line. Either ".py" or ".pdf". 

    """
    contained_filepaths = list(map(lambda contained_file: contained_file.code_filepath, contained_codes))    
    not_contained = []
    for filepath in code_filepaths:
        if not filepath in contained_filepaths:
           not_contained.append(filepath)
    return not_contained


def create_appendices_with_code(appendix_dir, code_filepaths, extension, project_nr, root_dir):
    """Creates the latex appendix files in with relevant codes included.

    :param appendix_dir: 
    :param code_filepaths: 
    :param extension: The file extension of the file that is sought in the appendix line. Either ".py" or ".pdf". 
    :param project_nr: The number  indicating which project this code pertains to. 
    :param root_dir: The root directory of this repository. 

    """
    appendix_filenames = []
    appendix_reference_index = 0

    for code_filepath in code_filepaths:
        latex_relative_filepath = f'latex/project{project_nr}/../../{code_filepath[len(root_dir):]}'
        content = []
        filename = get_filename_from_dir(code_filepath)
        content = create_section(appendix_reference_index, filename, content)
        inclusion_command = get_latex_inclusion_command(extension, latex_relative_filepath)
        content.append(inclusion_command)
        overwrite_content_to_file(content, f'{appendix_dir}Auto_generated_{extension[1:]}_App{appendix_reference_index}.tex', False)
        appendix_filenames.append(f'Auto_generated_{extension[1:]}_App{appendix_reference_index}.tex')
        appendix_reference_index = appendix_reference_index+1
    return appendix_filenames
    
    
def create_section(appendix_reference_index, code_filename, content):
    """

    :param appendix_reference_index: 
    :param code_filename: 
    :param content: 

    """
    # write section
    left ="\section{Appendix "
    middle = code_filename.replace("_","\_")
    right = "}\label{app:"
    end = "}" # TODO: update appendix reference index
    content.append(f'{left}{middle}{right}{appendix_reference_index}{end}')
    return content
    
    
def overwrite_content_to_file(content, filepath, content_has_newlines=True):
    """Writes the content of an appendix to a new appendix

    :param content: 
    :param filepath: 
    :param content_has_newlines:  (Default value = True)

    """
    with open(filepath,'w') as f:
        for line in content:
            if content_has_newlines:
                f.write(line)
            else:
                f.write(line+'\n')


def get_appendix_tex_code(main_latex_filename):
    """gets the latex appendix code from the main tex file.

    :param main_latex_filename: Name of the main latex document of this project number 

    """
    main_tex_code = read_file(main_latex_filename)
    start =  "\\begin{appendices}"
    end = "\end{appendices}"
    start_index = get_index_of_substring_in_list(main_tex_code, start)+1
    end_index = get_index_of_substring_in_list(main_tex_code, end)
    return main_tex_code, start_index, end_index, main_tex_code[start_index:end_index]


def get_index_of_substring_in_list(lines, target_substring):
    """

    :param lines: 
    :param target_substring: 

    """
    for i in range(0, len(lines)):
        if target_substring in lines[i]:
            if not line_is_commented(lines[i], target_substring):
                return i
        

def update_appendix_tex_code(appendix_filename, project_nr):
    """Includes the appendices as latex commands in the tex code string

    :param appendix_filename: 
    :param project_nr: The number  indicating which project this code pertains to. 

    """
    left = "\input{latex/project"
    middle = "/Appendices/"
    right = "} \\newpage\n"
    return f'{left}{project_nr}{middle}{appendix_filename}{right}'
        
        
def substitute_appendix_code(end_index, main_tex_code, start_index, updated_appendices_tex_code):
    """Replaces the old latex code that include the appendices with the new latex
    commands that include the appendices in the latex report.

    :param end_index: 
    :param main_tex_code: 
    :param start_index: 
    :param updated_appendices_tex_code: 

    """
    updated_main_tex_code = main_tex_code[0:start_index]+updated_appendices_tex_code+main_tex_code[end_index:]
    return updated_main_tex_code
    

def get_filename_from_dir(path):
    """

    :param path: 

    """
    return path[path.rfind("/")+1:]


def get_script_dir():
    """returns the directory of this script regardles of from which level the code is executed"""
    return os.path.dirname(__file__)
	

class Appendix_with_code:
    """stores in which appendix file and accompanying line number in the appendix in which a code file is
    already included. Does not take into account whether this appendix is in the main tex file or not


    """
    def __init__(self, code_filepath, appendix_filepath, appendix_content, file_line_nr, extension):
        self.code_filepath = code_filepath
        self.appendix_filepath = appendix_filepath
        self.appendix_content = appendix_content
        self.file_line_nr = file_line_nr
        self.extension = extension
        
        
class Appendix:
    """stores in appendix files and type of appendix."""
    def __init__(self, appendix_filepath, appendix_content, appendix_type, code_filename=None, appendix_inclusion_line=None):
        self.appendix_filepath = appendix_filepath
        self.appendix_filename = get_filename_from_dir(self.appendix_filepath)
        self.appendix_content = appendix_content
        self.appendix_type = appendix_type # TODO: perform validation of input values
        self.code_filename = code_filename
        self.appendix_inclusion_line = appendix_inclusion_line