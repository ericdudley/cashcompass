package format

import (
	"fmt"

	"golang.org/x/text/language"
	"golang.org/x/text/message"
)

var printer = message.NewPrinter(language.English)

// Cents formats cents as a signed dollar amount with an explicit + or - prefix,
// e.g. "+$1,234.56" or "-$1,234.56".
func Cents(cents int) string {
	sign := "+"
	abs := cents
	if cents < 0 {
		sign = "-"
		abs = -cents
	}
	return printer.Sprintf("%s$%.2f", sign, float64(abs)/100)
}

// CentsAbs formats cents as an unsigned dollar amount, e.g. "$1,234.56".
func CentsAbs(cents int) string {
	if cents < 0 {
		cents = -cents
	}
	return printer.Sprintf("$%.2f", float64(cents)/100)
}

// CentsDollars formats cents as a standard dollar amount, e.g. "$1,234.56" or
// "-$1,234.56". Positive values have no sign prefix.
func CentsDollars(cents int) string {
	if cents < 0 {
		return printer.Sprintf("-$%.2f", float64(-cents)/100)
	}
	return printer.Sprintf("$%.2f", float64(cents)/100)
}

// CentsInput returns the absolute decimal string suitable for HTML number
// inputs, e.g. "1234.56".
func CentsInput(cents int) string {
	if cents < 0 {
		cents = -cents
	}
	return fmt.Sprintf("%.2f", float64(cents)/100)
}
