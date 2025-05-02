#
# emulator front-end communicates with the G15 model via a command queue
#
# the queue transfers commands from the user interface into the G15 model
#
# message format:
# [MESG_ID, option1, option2]
#
#
# G15 internal command/message handler
#
class G15Cmds:
    def __init__(self, g15):
        self.g15 = g15
        self.cpu = self.g15.cpu
        self.emul = self.g15.emul
        
        # following dictionary defines possible queue message types
        self.messagetypes = {
            "dc": self.cpu.button_dc_h,
            "enable": self.cpu.sw_enable_h,
            "tape": self.cpu.sw_tape_h,
            "compute": self.cpu.sw_compute_h,
            "run": self.cpu.cmd_run
        }

    def do_cmd(self):
        # 
        # check if a command message is available in the queue
        #
        while not self.emul.qcmd.empty():
            #
            # have a command from the user interface to the G15
            #
            message = ''
            try:
                message = self.emul.qcmd.get()
                cmd = message[0]
                option = message[1]
                handler = self.messagetypes[cmd]
                handler(option)
            except:
                print("Internal error: ", message)
