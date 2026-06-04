from pywinauto import Desktop
import time

d = Desktop(backend='uia')
w = d.window(title='WeFlow')
w.set_focus()
time.sleep(0.5)

def dump(ctrl, depth=0):
    try:
        name = ctrl.element_info.name
        ctrl_type = ctrl.element_info.control_type
        if depth < 4:
            if name or ctrl_type in ['Button','Edit','Text','CheckBox','Hyperlink']:
                display = name[:80] if name else ''
                print('  '*depth + f'{ctrl_type}: {display}')
        for child in ctrl.children():
            dump(child, depth+1)
    except:
        pass

dump(w)
