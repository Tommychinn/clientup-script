#!/usr/bin/env python3
"""The Pre-Call Engagement Flow decision model.

Nothing here holds message text. Every message and every direction line is
identified by a leading substring, and `build-precall.py` resolves that against
the live Notion block tree — so the words on the page are always Tommy's, and a
reworded source fails the build instead of silently shipping stale copy.
"""

# ---------------------------------------------------------------------------
# Messages: id -> the opening words of the quote block in Notion.
# Must match exactly one quote block.
# ---------------------------------------------------------------------------
MESSAGES = {
    'OWNER_BIZ_OPEN':   'Hi [name], this is [your name] from Insider Group. I checked',
    'OWNER_PERS_OPEN':  "Hi [name], this is [your name] from Insider Group. I see you're running a business",
    'OWNER_PERS_NOWEB': 'OK. As far as you’re aware at this point',
    'OWNER_PERS_WEB':   'Okay, from your website it seems like your business is already well established',
    'Q1':               'Ok, makes sense. Do you already know quite a bit about PPL',
    'Q2':               'Ok. Do you already run lead gen internally',
    'R1':               'Ok, well we’ve created a ton of resources about the business model. Given you already know quite a bit about it, here are',
    'R2':               'Ok, well we’ve created a ton of resources about the business model. Given that you’re early stage exploring',
    'R3':               'Ok, well we’ve created a ton of resources about the business model. Given you’re already running lead gen internally',
    'R4':               'Ok, well we’ve created a ton of resources about the business model. Given you’re looking to build lead gen internally',
    'R5':               'Ok, well we’ve created a ton of resources about the business model. Given you’re already in the marketing space',
    'R6':               'Ok, well we’ve created a ton of resources about PPL. Given you already know quite a bit about it, but are also looking',
    'R7':               'Ok, well we’ve created a ton of resources about the business model. Given you’re quite new to it, but also looking',
    'MKT_AGENCY_ECOM':  'Hi [name], this is [your name] from Insider Group. I saw from **xyz.com**** **you’re in Ecom',
    'MKT_AGENCY_NICHE': 'Hi [name], this is [your name] from Insider Group. I saw from **xyz.com**** **you’re already running marketing for',
    'MKT_PERS_OPEN':    "Hi [name], this is [your name] from Insider Group. I see you're working as a marketer",
    'MKT_EMPLOYED':     'Ok, makes sense. And so the idea is build a pay per lead business on the side',
    'MKT_FREELANCE':    "Ok, is that just because you're just getting started",
    'MKT_WEB_ECOM':     "Ok, so you're in ecom. Are you already doing any PPL",
    'MKT_WEB_NICHE':    "Ok, so you're already working in industries that typically operate on a pay-per-lead basis",
    'N5_OPEN':          "Hi [name], this is [your name] from Insider Group. I saw you're looking to build a pay per lead business",
}

# ---------------------------------------------------------------------------
# Direction lines: id -> opening words of the text block in Notion.
# These are the blue lines above each message — Tommy's own instructions.
# ---------------------------------------------------------------------------
NOTES = {
    'OPEN_CHECK_SITE':  '**Opening message (check their website first):**',
    'OPEN':             '**Opening message:**',
    'IF_NO_WEBSITE':    '**If NO (no website):**',
    'IF_YES_WEBSITE':   '**If YES (they share a website):** review the website before replying',
    'SEND_Q1':          '**Send Q1:**',
    'SEND_Q2':          '**Send Q2:**',
    'KNOWS_R1':         '**If they already know quite a bit — send R1:**',
    'EARLY_R2':         "**If they're just looking into it — send R2:**",
    'RUNNING_R3':       '**If already running lead gen internally — send R3:**',
    'STARTING_R4':      '**If just looking to start — send R4:**',
    'KNOWS_R6':         '**If they already know quite a bit — send R6:**',
    'STARTING_R7':      '**If just looking to start — send R7:**',
    'MKT_OPEN_EXAMPLES': '**Opening message — make a comment / ask a question on something specific from their website. Examples:**',
    'MKT_ECOM_LABEL':   '**Ecom agency:**',
    'MKT_NICHE_LABEL':  '**Agency in any niche where people already do PPL',
    'AFTER_REPLY_R5':   '**After their reply — send R5:**',
    'MKT_EMPLOYED_IF':  '**If "no, I\'m working at someone else\'s company"',
    'MKT_FREELANCE_IF': '**If no website, but working for themselves',
    'MKT_FOLLOWUP_Q1':  '**Follow up Q (for either reply above) — send Q1:**',
    'MKT_IF_YES_SITE':  '**If YES (they share a website):** ask something in detail about their business',
    'MKT_WEB_ECOM_LBL': '**Ecom:**',
    'MKT_WEB_NICHE_LBL': '**Niche that typically runs PPL:**',
    'N5_STILL_LOOKING': '**If still looking at models — send Q1.',
}

# ---------------------------------------------------------------------------
# Questions the rep answers, in order. `when` gates a question on earlier
# answers; a question only appears once everything it depends on is answered.
#
# There is deliberately no question for the ecom / PPL-niche split. The source
# offers those as two example openings for the rep to choose between, not as a
# branch in the conversation, so both are shown inside the same step.
# ---------------------------------------------------------------------------
QUESTIONS = [
    {'id': 'segment', 'label': 'Prospect segment', 'options': [
        {'v': 'owner',    'l': '🏢 Business owner'},
        {'v': 'marketer', 'l': '📈 Marketer / agency'},
        {'v': 'nine5',    'l': '💼 Nine-to-fiver'},
    ]},

    {'id': 'ownerBooked', 'label': 'How they booked', 'when': {'segment': ['owner']}, 'options': [
        {'v': 'business', 'l': 'Business email'},
        {'v': 'personal', 'l': 'Personal email'},
    ]},
    {'id': 'ownerWebsite', 'label': 'Do they have a business website?',
     'when': {'segment': ['owner'], 'ownerBooked': ['personal']}, 'options': [
        {'v': 'no',  'l': 'No website'},
        {'v': 'yes', 'l': 'They shared one'},
    ]},
    {'id': 'ownerIntent', 'label': 'What they say they want', 'when': [
        {'segment': ['owner'], 'ownerBooked': ['business']},
        {'segment': ['owner'], 'ownerBooked': ['personal'], 'ownerWebsite': ['no', 'yes']},
     ], 'options': [
        {'v': 'ppl',      'l': 'Pay-per-lead business'},
        {'v': 'internal', 'l': 'Leads for their own business'},
        {'v': 'both',     'l': 'Both'},
    ]},
    {'id': 'ownerPplKnow', 'label': 'How well they know PPL',
     'when': {'segment': ['owner'], 'ownerIntent': ['ppl']}, 'options': [
        {'v': 'knows', 'l': 'Knows quite a bit'},
        {'v': 'early', 'l': 'Just looking into it'},
    ]},
    {'id': 'ownerInternal', 'label': 'Do they already run lead gen?',
     'when': {'segment': ['owner'], 'ownerIntent': ['internal']}, 'options': [
        {'v': 'already',  'l': 'Already running it'},
        {'v': 'starting', 'l': 'Looking to start'},
    ]},
    {'id': 'ownerBothKnow', 'label': 'How well they know PPL',
     'when': {'segment': ['owner'], 'ownerIntent': ['both']}, 'options': [
        {'v': 'knows', 'l': 'Knows quite a bit'},
        {'v': 'early', 'l': 'Quite new to it'},
    ]},

    {'id': 'mktBooked', 'label': 'How they booked', 'when': {'segment': ['marketer']}, 'options': [
        {'v': 'agency',   'l': "Agency's business email"},
        {'v': 'personal', 'l': 'Personal email'},
    ]},
    {'id': 'mktReply', 'label': 'How they reply',
     'when': {'segment': ['marketer'], 'mktBooked': ['personal']}, 'options': [
        {'v': 'employed',  'l': "At someone else's company"},
        {'v': 'freelance', 'l': 'Own clients, no website'},
        {'v': 'website',   'l': 'They shared a website'},
    ]},

    {'id': 'n5Know', 'label': 'How well they know the model',
     'when': {'segment': ['nine5']}, 'options': [
        {'v': 'knows', 'l': 'Knows quite a bit'},
        {'v': 'early', 'l': 'Early stage exploring'},
    ]},
]

# ---------------------------------------------------------------------------
# Sequence rules. Every rule whose `match` is satisfied contributes its steps,
# in list order, so the flow grows message by message as the rep answers.
#
# Each rule is gated on the FEWEST answers that actually determine its message.
# The opening message for a business owner on a personal email is the same
# whether or not they have a website, so it must appear the moment those two
# are chosen — not wait for a third answer it doesn't depend on.
#
# A step is either one message, or a set of variants the rep picks between.
# ---------------------------------------------------------------------------
def step(note, msg):
    return {'note': note, 'msg': msg}


def choice(note, *variants):
    return {'note': note, 'variants': [{'label': l, 'msg': m} for l, m in variants]}


SEQUENCE = [
    # --- business owner: opening ---
    {'match': {'segment': ['owner'], 'ownerBooked': ['business']},
     'steps': [step('OPEN_CHECK_SITE', 'OWNER_BIZ_OPEN')]},
    {'match': {'segment': ['owner'], 'ownerBooked': ['personal']},
     'steps': [step('OPEN', 'OWNER_PERS_OPEN')]},
    {'match': {'segment': ['owner'], 'ownerBooked': ['personal'], 'ownerWebsite': ['no']},
     'steps': [step('IF_NO_WEBSITE', 'OWNER_PERS_NOWEB')]},
    {'match': {'segment': ['owner'], 'ownerBooked': ['personal'], 'ownerWebsite': ['yes']},
     'steps': [step('IF_YES_WEBSITE', 'OWNER_PERS_WEB')]},

    # --- business owner: intent branches ---
    {'match': {'segment': ['owner'], 'ownerIntent': ['ppl', 'both']},
     'steps': [step('SEND_Q1', 'Q1')]},
    {'match': {'segment': ['owner'], 'ownerIntent': ['internal']},
     'steps': [step('SEND_Q2', 'Q2')]},
    {'match': {'segment': ['owner'], 'ownerIntent': ['ppl'], 'ownerPplKnow': ['knows']},
     'steps': [step('KNOWS_R1', 'R1')]},
    {'match': {'segment': ['owner'], 'ownerIntent': ['ppl'], 'ownerPplKnow': ['early']},
     'steps': [step('EARLY_R2', 'R2')]},
    {'match': {'segment': ['owner'], 'ownerIntent': ['internal'], 'ownerInternal': ['already']},
     'steps': [step('RUNNING_R3', 'R3')]},
    {'match': {'segment': ['owner'], 'ownerIntent': ['internal'], 'ownerInternal': ['starting']},
     'steps': [step('STARTING_R4', 'R4')]},
    {'match': {'segment': ['owner'], 'ownerIntent': ['both'], 'ownerBothKnow': ['knows']},
     'steps': [step('KNOWS_R6', 'R6')]},
    {'match': {'segment': ['owner'], 'ownerIntent': ['both'], 'ownerBothKnow': ['early']},
     'steps': [step('STARTING_R7', 'R7')]},

    # --- marketer / agency ---
    {'match': {'segment': ['marketer'], 'mktBooked': ['agency']},
     'steps': [choice('MKT_OPEN_EXAMPLES',
                      ('MKT_ECOM_LABEL', 'MKT_AGENCY_ECOM'),
                      ('MKT_NICHE_LABEL', 'MKT_AGENCY_NICHE')),
               step('AFTER_REPLY_R5', 'R5')]},
    {'match': {'segment': ['marketer'], 'mktBooked': ['personal']},
     'steps': [step('OPEN', 'MKT_PERS_OPEN')]},
    {'match': {'segment': ['marketer'], 'mktBooked': ['personal'], 'mktReply': ['employed']},
     'steps': [step('MKT_EMPLOYED_IF', 'MKT_EMPLOYED'),
               step('MKT_FOLLOWUP_Q1', 'Q1'),
               step('AFTER_REPLY_R5', 'R5')]},
    {'match': {'segment': ['marketer'], 'mktBooked': ['personal'], 'mktReply': ['freelance']},
     'steps': [step('MKT_FREELANCE_IF', 'MKT_FREELANCE'),
               step('MKT_FOLLOWUP_Q1', 'Q1'),
               step('AFTER_REPLY_R5', 'R5')]},
    {'match': {'segment': ['marketer'], 'mktBooked': ['personal'], 'mktReply': ['website']},
     'steps': [choice('MKT_IF_YES_SITE',
                      ('MKT_WEB_ECOM_LBL', 'MKT_WEB_ECOM'),
                      ('MKT_WEB_NICHE_LBL', 'MKT_WEB_NICHE')),
               step('AFTER_REPLY_R5', 'R5')]},

    # --- nine-to-fiver: no branch before the first two messages ---
    {'match': {'segment': ['nine5']},
     'steps': [step('OPEN', 'N5_OPEN'), step('N5_STILL_LOOKING', 'Q1')]},
    {'match': {'segment': ['nine5'], 'n5Know': ['knows']},
     'steps': [step('KNOWS_R1', 'R1')]},
    {'match': {'segment': ['nine5'], 'n5Know': ['early']},
     'steps': [step('EARLY_R2', 'R2')]},
]

# Messages that mention the prospect's niche, so the niche input only appears
# when the selected flow actually needs it.
NEEDS_NICHE = ['MKT_AGENCY_NICHE']
# Messages that mention their website, so the website input appears only then.
NEEDS_SITE = ['OWNER_BIZ_OPEN', 'MKT_AGENCY_ECOM', 'MKT_AGENCY_NICHE']
