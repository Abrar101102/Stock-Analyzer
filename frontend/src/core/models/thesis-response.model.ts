export interface ThesisResponseModel {
symbol:string;
verdict:"Buy" | "Sell" | "Hold" | null;
summary:string;
signals:Signal;
generated_at:string
}

export interface Signal {
  fundamental:string;
  technical:string;
  sentiment:string;
  valuation:string;
}