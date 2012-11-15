import sublime, sublime_plugin
import os, tempfile

PACKAGE_SETTINGS = "QuickPrint.sublime-settings"

DEF_COMPUTER = sublime.load_settings(PACKAGE_SETTINGS).get("comp_name", \
    False)
if not DEF_COMPUTER:
    DEF_COMPUTER = os.environ['COMPUTERNAME']
DEF_PRINTER = sublime.load_settings(PACKAGE_SETTINGS).get("default_printer", \
    "PrimoPDF")
# Advanced, Print Processor.. Text (from RAW) for PrimoPDF

#DEF_COMPUTER = "ANDYCOMPAQ"
#DEF_PRINTER = "PrimoPDF"

LINES_PPAGE = sublime.load_settings(PACKAGE_SETTINGS).get("lines_ppage", \
    False)
BLANK_HEAD = sublime.load_settings(PACKAGE_SETTINGS).get("blank_lines_head", \
    False)
SPACES_LEFT = sublime.load_settings(PACKAGE_SETTINGS).get("spaces_left", \
    False)

try:
    init_printer = "net use lpt1 \\\\" + DEF_COMPUTER + "\\" + DEF_PRINTER + \
        " /persistent:yes"
    os.system(init_printer)
    init_printer = True
except Exception:
    sublime.status_message('Printer not configured correctly.')
    init_printer = False

class QuickPrint(sublime_plugin.WindowCommand):
    def run(self):
        if init_printer:
            vw = self.window.active_view()
            vw_filename = vw.file_name() or 'quickprinttemp.txt'
            vw_base = os.path.basename(vw_filename)
            tempd = tempfile.gettempdir()
            vw_firstbase, vw_ext = os.path.splitext(vw_base)
            if not vw_ext or vw_ext != '.txt':
                vw_filename = vw_firstbase + '.txt'
            else:
                vw_filename = vw_base
            vw_filename = tempd + os.sep + vw_filename
            tempf = open(vw_filename, 'w')
            x = 0
            if BLANK_HEAD is not False:
                tempf.write('\n' * BLANK_HEAD)
                x = x + BLANK_HEAD
            for line in vw.split_by_newlines(sublime.Region(0, vw.size())):
                if x and LINES_PPAGE and (x % LINES_PPAGE) == 0:
                    tempf.write('\f')
                    if BLANK_HEAD is not False:
                        tempf.write('\n' * BLANK_HEAD)
                        x = x + BLANK_HEAD
                if SPACES_LEFT is not False:
                    tempf.write(" " * SPACES_LEFT)
                tempf.write(vw.substr(line) + '\n')
                x = x + 1
            tempf.close()

            #os.system('type system_ex.txt > LPT1')
            os.system("type " + vw_filename.replace('\\', '\\\\') + " > LPT1")
        else:
            sublime.status_message('Printer not configured correctly.')
