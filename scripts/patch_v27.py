#!/usr/bin/env python3
"""v27: reviewer feedback (Nov 20), Customer Service Bundle Square links, InsightDesk demo (15 tools in the Demo Lab)."""
import sys, os
p = os.path.join(sys.argv[1] if len(sys.argv) > 1 else "staging", "index.html")
s = open(p, encoding="utf-8").read()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (a[:80], c)
    s = s.replace(a, b)

# 1. heading entity typo from the Title Case pass
rep("Property &Amp; Hospitality Tools", "Property &amp; Hospitality Tools")

# 2. clearer cost FAQ
rep("<details><summary>How Much Does a Project Cost?</summary><p>Desk product setups are a one-time fee of $500–$3,500, with low monthly license &amp; support plans from $50. The Workflow &amp; Automation Assessment is $750 (virtual), custom pilots start at $3,500, and the Care &amp; Growth Plan starts at $150/month.",
    "<details><summary>How Much Does a Project Cost?</summary><p>The Free Workflow Audit costs nothing: a 30-minute call and a one-page summary. If you want a deeper review, the Workflow &amp; Automation Assessment is $750 (virtual) and is credited toward a build started within 60 days. Desk tool setups are a one-time fee of $500–$3,500, with monthly license &amp; support plans from $50 per tool. A Booking Website is $1,500. Custom pilots start at $3,500, and the Care &amp; Growth Plan starts at $150/month.")

# 3. bundle cards show the same holiday monthly rate as the order dialog
rep("then $120/mo for all three on Essentials.", 'then <span class="bmo" data-mo="120">$120/mo</span> for all three on Essentials, plus usage.')
rep("then $100/mo for both tools on Essentials.", 'then <span class="bmo" data-mo="100">$100/mo</span> for both tools on Essentials, plus usage.')
rep("""el.innerHTML=`<s class="was">${money(p)}</s> ${money(s)}`;""",
    """el.innerHTML=`<s class="was">${money(p)}</s> ${money(s)}`; const mo=el.closest("p").querySelector(".bmo"); if(mo){ const m=+mo.dataset.mo; mo.innerHTML=`${money(saleAmt(m))}/mo for the first 12 months (then ${money(m)}/mo)`; }""")

# 4. payment is collected at checkout, not at kickoff
rep("the first at kickoff, then 30 and 60 days later", "the first at checkout, then 30 and 60 days later", 3)

# 5. installments: show all three amounts; the last one makes the total exact
rep("""if(setup) parts.push(plan==="3 monthly payments" ? `<b>Due at kickoff:</b> ${money2(Math.ceil(setup/30)*10)} (first of 3 payments)` : `<b>Due at kickoff:</b> ${money2(setup)}${it.quote?" (starting price; final amount is in your written quote)":""}`);""",
    """if(setup){ const first=Math.ceil(setup/30)*10, last=setup-2*first; parts.push(plan==="3 monthly payments" ? `<b>Due today at checkout:</b> ${money2(first)} (first of 3 payments: ${money2(first)} today, ${money2(first)} in 30 days and ${money2(last)} in 60 days, ${money2(setup)} in total)` : `<b>Due today at checkout:</b> ${money2(setup)}${it.quote?" (starting price; final amount is in your written quote)":""}`); }""")

# 6. Customer Service Bundle pays online now (Square links for $2,700 holiday and $3,000 regular; 3 payments use $900 / $1,000)
rep('csbundle:{name:"Customer Service Bundle: ChatDesk + LeadDesk + ReviewDesk setup", price:3000, monthly:120, invoice:true},   // invoice until its Square links exist',
    'csbundle:{name:"Customer Service Bundle: ChatDesk + LeadDesk + ReviewDesk setup", price:3000, monthly:120},')
rep('squareLinks: {"300":', 'squareLinks: {"2700":"https://square.link/u/5yteuPVm","3000":"https://square.link/u/3yfkgqPT","300":')

# 7. InsightDesk joins the Demo Lab (15 tools)
rep("""    checks:()=>["The owner approves any change to due dates","Payments are matched before reminders stop","Card numbers are never typed into messages"]}
};""", """    checks:()=>["The owner approves any change to due dates","Payments are matched before reminders stop","Card numbers are never typed into messages"]},
  insight:{sector:"Owners & Managers", title:"InsightDesk", label:"Owner insights", short:"Weekly summary",
    samples:["How did bookings do this week compared to last week?","Which leads haven't gotten a reply in 2 days?","Reviews dropped this month. What changed?"],
    cats:[["Weekly summary",/this week|last week|compared|summary|how did|numbers/i,"Weekly summary · owner"],["Follow-ups needed",/no reply|haven't|not answered|waiting|follow ?up|2 days/i,"Follow-up list · front desk"],["Trend question",/dropped|down|up |changed|why|trend|month/i,"Trend review · owner"]],
    def:["Owner question","Owner dashboard"],
    urgent:/urgent|today|dropped sharply|refund/i,
    reply:(d)=>d.cat==="Weekly summary"?"Bookings are up 12% on last week (46 vs. 41). Tuesday was the slowest day; the full summary is in your inbox.":d.cat==="Follow-ups needed"?"3 leads are waiting more than 2 days. I've listed them with phone numbers so the front desk can call today.":"Reviews fell from 18 to 11 this month. Fewer review requests went out after the week-3 schedule change; turning them back on is the quickest fix.",
    checks:()=>["Numbers come straight from your own tools","Summaries say what changed and what needs attention","You decide what to act on"]}
};""")
open(p, "w", encoding="utf-8").write(s)
print("v27 applied to", p)
