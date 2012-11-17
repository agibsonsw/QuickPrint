import sublime, sublime_plugin
import os, subprocess, tempfile, sys

PACKAGE_SETTINGS = "QuickPrint.sublime-settings"
PLATFORM = sublime.platform()   # may be "osx", "linux" or "windows"

COMPUTER = sublime.load_settings(PACKAGE_SETTINGS).get("comp_name", \
    os.environ['COMPUTERNAME'])
PRINTER = sublime.load_settings(PACKAGE_SETTINGS).get("printer_name", False)
# osx or linux:
QUEUE = sublime.load_settings(PACKAGE_SETTINGS).get("queue", False)

FILE_TITLE = sublime.load_settings(PACKAGE_SETTINGS).get("file_as_title", \
    False)
LINES_PPAGE = sublime.load_settings(PACKAGE_SETTINGS).get("lines_ppage", False)
BLANK_HEAD = sublime.load_settings(PACKAGE_SETTINGS).get("blank_lines_head", \
    False)
SPACES_LEFT = sublime.load_settings(PACKAGE_SETTINGS).get("spaces_left", False)
PAGE_NOS = sublime.load_settings(PACKAGE_SETTINGS).get("page_nos", False)
if PAGE_NOS is not False and not str(PAGE_NOS).isdigit():
    # if this setting is present it must be a (whole) number
    PAGE_NOS = False
LINE_NOS = sublime.load_settings(PACKAGE_SETTINGS).get("line_nos", False)

if PRINTER is not False and " " in PRINTER:
    # the printer name needs to be quoted if it contains any spaces 
    printer_cmd = "net use lpt1 \\\\" + COMPUTER + "\\" + \
    '""' + PRINTER + '""' + "/persistent:yes"
elif PRINTER is not False:
    printer_cmd = "net use lpt1 \\\\" + COMPUTER + "\\" + PRINTER + \
        " /persistent:yes"
else:
    printer_cmd = ""

init_printer = True
if PLATFORM == "windows":
    try:
        # use LPT1 if available
        subprocess.check_call("net use lpt1", shell=False)
    except subprocess.CalledProcessError:
        # printer not yet assigned
        try:
            if printer_cmd != "":
                subprocess.check_call(printer_cmd, shell=False)
        except subprocess.CalledProcessError:
            sublime.status_message('Printer not configured correctly.')
            init_printer = False
        except Exception as e:
            sublime.status_message('A system error occurred.')
            print(sys.exc_info())
            init_printer = False

class QuickPrint(sublime_plugin.WindowCommand):
    def run(self):
        if init_printer:
            add_title = False
            vw = self.window.active_view()
            if FILE_TITLE is not False:
                vw_title = vw.file_name()
                if vw_title != '':
                    add_title = True
            vw_filename = vw.file_name() or 'quickprinttemp.txt'
            vw_base = os.path.basename(vw_filename)
            vw_firstbase, vw_ext = os.path.splitext(vw_base)
            if not vw_ext or vw_ext != '.txt':
                vw_filename = vw_firstbase + '.txt'
            else:
                vw_filename = vw_base
            vw_filename = tempfile.gettempdir() + os.sep + vw_filename
            tempf = open(vw_filename, 'w')
            x = 0; page = 1
            if add_title:
                tempf.write(" " * SPACES_LEFT)
                tempf.write(vw_title + '\n\n')
                x = x + 2
                if BLANK_HEAD is not False and BLANK_HEAD > 2:
                    tempf.write('\n' * (BLANK_HEAD - 2))
                    x = x + (BLANK_HEAD - 2)
            elif BLANK_HEAD is not False:
                tempf.write('\n' * BLANK_HEAD)
                x = x + BLANK_HEAD
            sel = vw.sel()[0]
            toPrint = sel if not sel.empty() else sublime.Region(0, vw.size())
            for line in vw.split_by_newlines(toPrint):
                if x and LINES_PPAGE and (x % LINES_PPAGE) == 0:
                    # between pages..
                    if PAGE_NOS is not False:
                        tempf.write('\n' * PAGE_NOS)
                        tempf.write(" " * SPACES_LEFT)
                        tempf.write("%d" % page)
                        page += 1
                    tempf.write('\f')
                    if BLANK_HEAD is not False:
                        tempf.write('\n' * BLANK_HEAD)
                        x = x + BLANK_HEAD
                if SPACES_LEFT is not False:
                    tempf.write(" " * SPACES_LEFT)
                if LINE_NOS:
                    lineno, _ = vw.rowcol(line.begin())
                    tempf.write("%4d  " % (lineno + 1))
                tempf.write(vw.substr(line) + '\n')
                x = x + 1
            tempf.close()
            vw_filename = vw_filename.replace(' ', '_').replace('\\', '\\\\')
            if PLATFORM == "windows":
                #os.system('type system_ex.txt > LPT1')
                subprocess.call("type " + vw_filename + " > LPT1", shell=True)
            elif PLATFORM == "osx":
                # lp -d <queue name> <name of document>
                # lp <name of document> will send to default printer(?)
                if QUEUE is not False:
                    subprocess.call("lp -d " + QUEUE + " " + vw_filename)
                else:
                    subprocess.call("lp " + vw_filename)
            elif PLATFORM == "linux":
                if QUEUE is not False:
                    subprocess.call("lpr -P " + QUEUE + " " + vw_filename)
                else:
                    subprocess.call("lpr " + vw_filename)
        else:
            sublime.status_message('Printer not configured correctly.')

class QuickPrintReset(sublime_plugin.WindowCommand):
    def run(self):
        global init_printer
        if PLATFORM != "windows":
            sublime.status_message('Command only applies to Windows.')
            return
        init_printer = False
        try:
            # check if LPT1 available
            subprocess.check_call("net use lpt1", shell=False)
        except subprocess.CalledProcessError:
            # printer not yet assigned
            try:
                subprocess.check_call(printer_cmd, shell=False)
                init_printer = True
                sublime.status_message('Printer assigned.')
            except subprocess.CalledProcessError:
                sublime.status_message('Unable to assign printer.')
            except Exception as e:
                sublime.status_message('A system error occurred.')
                print(sys.exc_info())
        else:
            try:
                # change printer assignment
                subprocess.check_call("net use LPT1: /d", shell=False)
                subprocess.check_call(printer_cmd, shell=False)
                init_printer = True
                sublime.status_message("Printer re-assigned.")
            except subprocess.CalledProcessError:
                sublime.status_message("Unable to re-assign printer.")
            except Exception as e:
                sublime.status_message('A system error occurred.')
                print(sys.exc_info())