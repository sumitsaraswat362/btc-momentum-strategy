class RiskManager:
    def __init__(self, stop_loss_pct=0.05):
        self.stop_loss_pct = stop_loss_pct  # 5% Max Loss
        self.active = True

    def evaluate(self, initial_cash, current_cash):
        loss = (initial_cash - current_cash) / initial_cash
        if loss >= self.stop_loss_pct:
            print(f"!!! CRITICAL RISK: {loss:.2%} loss detected. TRIGGERING KILL SWITCH !!!")
            self.active = False
            return False
        return True