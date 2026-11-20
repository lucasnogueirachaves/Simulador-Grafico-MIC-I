class Mmux:
    
    def calcular_proximo_mpc(self, mpc_atual, cond, addr, flag_n: bool, flag_z: bool):
        
        desviar = False
        
        if cond == 0:
            desviar = False
        elif cond == 1:
            if flag_n:
                desviar = True
        elif cond == 2:
            if flag_z:
                desviar = True
        elif cond == 3:
            desviar = True
            
        if desviar:
            return addr & 0xFF
        else:
            return (mpc_atual + 1) & 0xFF