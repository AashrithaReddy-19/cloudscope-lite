from math import sqrt
def _model(v):
 n=len(v);mx=(n-1)/2;my=sum(v)/n;d=sum((i-mx)**2 for i in range(n));s=sum((i-mx)*(y-my) for i,y in enumerate(v))/d if d else 0;return s,my-s*mx
def forecast(records):
 v=[float(r["cost"]) for r in sorted(records,key=lambda r:r["date"])];n=len(v)
 if n<6:raise ValueError("At least six chronological records are required.")
 s,b=_model(v);result={"linear_regression":[round(b+s*i,2) for i in range(n,n+3)],"moving_average":[round(sum(v[-3:])/3,2)]*3,"metrics":None,"limitations":["Forecasts extrapolate historical patterns and are not guarantees."]}
 if n>=12:
  split=int(n*.8);s,b=_model(v[:split]);actual=v[split:];pred=[b+s*i for i in range(split,n)];errors=[abs(a-p) for a,p in zip(actual,pred)];nz=[abs((a-p)/a) for a,p in zip(actual,pred) if a];result["metrics"]={"mae":round(sum(errors)/len(errors),4),"rmse":round(sqrt(sum(e*e for e in errors)/len(errors)),4),"mape":round(sum(nz)/len(nz)*100,4) if nz else None}
 return result
