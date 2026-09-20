from decimal import Decimal
def recommend(rows,total,scenario):
    output=[]; total=Decimal(str(total))
    for row in sorted(rows,key=lambda x:Decimal(x["estimated_cost"]),reverse=True)[:3]:
        issue="This resource is a leading cost contributor."
        suggestion="Review sizing, schedule and necessity before deployment."
        if row["resource_type"]=="aws_instance" and scenario=="low": suggestion="Schedule development instances during working hours and review instance size."
        output.append({"resource_name":row["resource_name"],"issue":issue,"suggestion":suggestion,"current_estimated_cost":row["estimated_cost"],"alternative_estimated_cost":None,"estimated_savings":None,"confidence":"medium","explanation":"Ranking uses the calculated resource costs; no alternative price was assumed."})
    return output

