'use strict';
var getFinancial = require( '../dispatchers/get-financial-values' );

var expensesModel = {
  values: {},

  expenseKeys: [
    'Retirement',
    'Transportation',
    'Entertainment',
    'Food',
    'Housing',
    'Other',
    'Healthcare'
  ],

  /**
   * Initializes this model
   * @param {object} expenses - object containing unformatted API values
   */
  init: function( expenses ) {
    this.values.stored = expenses;
  },

  /**
   * Takes model values and performs calculations
   */
  calc: function() {
    var model = this.values,
        financialValues = getFinancial.values();
    // monthly expenses
    model.totalMonthlyExpenses =
      Math.round( model.housing + model.food +
      model.transportation + model.healthcare +
      model.retirement + model.other + model.entertainment );

    model.monthlyLeftover = Math.round( financialValues.monthlySalary -
      model.totalMonthlyExpenses - financialValues.loanMonthly );

    this.values = model;
  },

  /**
   * Turns a salary number into a salary range for use in retrieving
   * the correct BLS expense values.
   * @param {number} salary - Number value of salary
   * @returns {string} salaryRange - String representing salary range
   */
  getSalaryRange: function( salary ) {
    var rangeFinder = {
      'less_than_5000': [ 0, 4999 ],
      '5000_to_9999':   [ 5000, 9999 ],
      '10000_to_14999': [ 10000, 14999 ],
      '15000_to_19999': [ 15000, 19999 ],
      '20000_to_29999': [ 20000, 29999 ],
      '30000_to_39999': [ 30000, 39999 ],
      '40000_to_49999': [ 40000, 49999 ],
      '50000_to_69999': [ 50000, 69999 ],
      '70000_or_more':  [ 70000, Infinity ]
    };
    for ( var key in rangeFinder ) {
      var arr = rangeFinder[key];
      if ( salary >= arr[0] && salary <= arr[1] ) {
        return key;
      }
    }
    return false;
  },

  resetCurrentValues: function( region, salary ) {
    for ( var x = 0; x < this.expenseKeys.length; x++ ) {
      var key = this.expenseKeys[x],
          expense = key.toLowerCase(),
          salaryRange = this.getSalaryRange( salary ),
          val = this.values.stored[key][region][salaryRange];

      this.values[expense] = Math.round( val / 12 );
    }
    this.calc();
  }

};

module.exports = expensesModel;