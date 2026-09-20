from decimal import Decimal
def evaluate_budget(cost,budget,warning_threshold_percentage=80,fail_when_exceeded=True):
    cost,budget=Decimal(str(cost)),Decimal(str(budget or 0))
    if budget<=0: return {"status":"NOT_CONFIGURED","budget":str(budget),"estimated_cost":str(cost),"budget_usage_percentage":None,"remaining_budget":None,"message":"Set a positive monthly budget to enable policy checks."}
    usage=cost/budget*100; status="FAIL" if cost>budget and fail_when_exceeded else ("WARNING" if usage>warning_threshold_percentage else "PASS")
    return {"status":status,"budget":str(budget),"estimated_cost":str(cost),"budget_usage_percentage":round(float(usage),2),"remaining_budget":str(budget-cost),"message":f"The estimated cost has reached {usage:.2f}% of the monthly budget."}

