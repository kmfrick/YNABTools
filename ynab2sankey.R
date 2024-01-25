library(readr)
library(dplyr)

data = read_csv("input.csv") %>%
  select(Inflow, Outflow, Payee, Category) %>%
  mutate(
    Inflow = as.numeric(gsub("[^0-9.]", "", Inflow)),
    Outflow = as.numeric(gsub("[^0-9.]", "", Outflow)),
    Amount = Inflow - Outflow
  ) %>%
  filter(!grepl("Transfer", Payee)) %>%
  filter(!grepl("Starting Balance", Payee))
# Open a text file for writing
output_file = file("temp_output.csv", "w")
cat(paste0("Input, Amount, Output\n"), file = output_file)
for (i in 1:nrow(data)) {
  # Extract values from the current row
  payee = data$Payee[i]
  amount = data$Amount[i]
  category = data$Category[i]
  category = ifelse(is.na(category), payee, category)

  # Check if the amount is positive or negative
  if (amount > 0) {
    cat(paste0(payee, ", ", amount, ", Income\n"), file = output_file)
  } else {
    cat(paste0("Income, ", -amount, ", ", category, "\n"), file = output_file)
  }
}

cashflow = sum(data$Inflow - data$Outflow)
if (cashflow > 0) {
  cat(paste0("Income, ", cashflow, ", Savings"), file = output_file)
} else {
  cat(paste0("Last Year's Savings, ", -cashflow, ", Income"), file = output_file)
}
close(output_file)
temp_output = read.csv("temp_output.csv", sep = ",", header = TRUE) %>%
  group_by(Input, Output) %>%
  summarise(Amount = sum(Amount))
def_output = file("output.txt", "w")
for (i in 1:nrow(temp_output)) {
  cat(paste0(temp_output$Input[i], " [", temp_output$Amount[i], "] ", temp_output$Output[i], "\n"), file = def_output)
}
close(def_output)

cat("Conversion completed. Output written to output.txt\n")
