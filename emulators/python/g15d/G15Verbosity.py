


verbosity_defs = {
    'cpu': {
        'value': 0,         # current verbosity value
        'loc': self.g15.cpu,
        'details': 1,
        'trace': 2,
        'utrace': 4,
        'debug': 8,
        'eb': 16,
        'ib': 32,
        'lb': 64,
        'd31': 128,
        'math': 256,
        'pn': 512,
        'stdout': 1024,
        'ar': 2048,
        'all': 0xffff,
        'clear': 0
    },
    'drum': {
        'value': 0,         # current verbosity value
        'loc': self.g15.drum,
        'create': 1,
        'op': 2,
        'precess': 4,
        'details': 8,
        'all': 0xffff,
        'clear': 0
    },
    'ptr': {
        'value': 0,         # current verbosity value
        'loc': self.g15.ptr,
        'mount': 1,
        'chksum': 2,
        'parse': 4,
        'all': 0xffff,        
        'clear': 0
    },
    'ptp': {
        'value': 0,         # current verbosity value
        'loc': self.g15.ptp,
        'debug': 1,
        'all': 0xffff,
        'clear': 0

    },
    'd31': {
        'value': 0,         # current verbosity value
        'loc': self.g15.cpu.cpu_d31,
        'multiply': 1,
        'divide': 2,
        'markret': 4,
        'd31': 8,
        'all': 0xffff,
        'clear': 0        
    },
    'io': {
        'value': 0,         # current verbosity value
        'loc': self.g15.iosys,
        'slowout': 2,
        'format': 4,
        'detail': 0xf,
        'all': 0xffff,
        'clear': 0
    }
}


class Verbosity:
    def __init__(self, g15):
        self.g15 = g15
        self.emul = g15.emul
        
    def find_entry(self, block, name):
        # ensure that block and name are both in dict
        if block not in verbosity_defs:
            self.emul.log.msg("Error: block: " + block + " not found")
            return None
        
        blockH = verbosity_defs[block]
        
        if name not in blockH:
            self.emul.log.msg("Error: selection is unknown")
            return None
        
        return blockH
            
    def activate(self, block, name):
        blockH = self.find_entry(block, name)
        if blockH is None:
            return

        if name == 'clear':
            blockH['value'] = 0
            return
            
        blockH['value'] |= blockH[name]
            
    def deactivate(self, block, name):
        blockH = self.find_entry(block, name)
        if blockH is None:
            return

        if name == 'clear':
            return
            
        blockH['value'] &= ~blockH[name]
        
    def get_value(self, block, name):
        blockH = self.find_entry(block, name)
        if blockH is None:
            return
        
        return blockH['value']
        
    def print_check(self, block, name):
        blockH = self.find_entry(block, name)
        if blockH is None:
            return   
        
        if blockH['value'] & blockH['name']:
            print("????")
