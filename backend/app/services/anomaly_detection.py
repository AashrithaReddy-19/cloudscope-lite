from math import sqrt
def _q(v,q):
 v=sorted(v);p=(len(v)-1)*q;lo=int(p);hi=min(lo+1,len(v)-1);return v[lo]+(v[hi]-v[lo])*(p-lo)
def detect(records,method="iqr"):
 rows=sorted(records,key=lambda r:r["date"]);v=[float(r["cost"]) for r in rows];out=[]
 if method=="iqr":q1,q3=_q(v,.25),_q(v,.75);g=q3-q1;bounds=[(q1-1.5*g,q3+1.5*g)]*len(rows)
 elif method=="rolling_zscore":
  bounds=[]
  for i in range(len(v)):
   prior=v[max(0,i-3):i]
   if len(prior)<3:bounds.append((None,None));continue
   mean=sum(prior)/3;std=sqrt(sum((x-mean)**2 for x in prior)/3);bounds.append((mean-2*std,mean+2*std))
 else:raise ValueError("Method must be iqr or rolling_zscore")
 for row,(low,high) in zip(rows,bounds):
  value=float(row["cost"])
  if low is not None and (value<low or value>high):out.append({"date":str(row["date"]),"actual_cost":value,"expected_range":[round(low,2),round(high,2)],"difference":round(value-(high if value>high else low),2),"detection_method":method,"explanation":"Statistical deviation; this does not establish fraud."})
 return out
