# coffee-shop-simulator
A cozy coffee shop simulator built with Python in 30 days.

## Project goal

Build a small Python coffee shop simulator step by step over 30 days.
Start with a simple, understandable game loop and expand it as the basics work.

## First milestone: budget and ingredients

The first playable milestone will let the player:

- See the current budget and stocks of coffee and milk.
- Buy coffee and milk at clearly displayed prices.
- Receive an explanation when a purchase exceeds the available budget.
- See the updated budget and ingredient stocks after a purchase.

Purchases should accept positive quantities only. Successful purchases deduct
their cost from the budget and add the purchased ingredients to stock; rejected
purchases leave both unchanged.

This milestone is complete when those actions work in a simple console menu.
The starting budget, prices, and ingredient units will be chosen during
implementation and displayed to the player.

## Later milestones

- Prepare drinks using ingredients.
- Serve visitors and track sales revenue.
- Save and load game progress.

This repository currently contains project documentation; game implementation
will follow in small, reviewable steps.
