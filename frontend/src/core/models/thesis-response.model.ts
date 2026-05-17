export interface ThesisResponseModel {
symbol:string;
verdict:"Buy" | "Sell" | "Hold" | null;
confidence: "High" | "Medium" | "Low" | null;
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