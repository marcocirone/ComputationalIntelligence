The goal of this lab is to learn a strategy to beat an opponent that plays following the optimal strategy, consisting in performing a move that makes the nim sum of all the rows not equal to 0. The possible moves the algorithm can exploit are:

- Taking the greatest possible number of matches from a single row
- Taking the number of matches that allows you to leave a specific row as full as possible
- Taking the number of matches that allows you to leave a specific row as empty as possible

The adopted strategy is a μ+σ strategy, where μ equals 20 and σ equals 40