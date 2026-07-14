const colors = {
  reset: "\x1b[0m",

  // backgrounds
  bgRed: "\x1b[41m",
  bgBlue: "\x1b[44m",
  bgGreen: "\x1b[42m",
  bgYellow: "\x1b[43m",
  bgGray: "\x1b[100m",

  // optional: text colors for contrast control
  black: "\x1b[30m",
  white: "\x1b[97m",
};

export function logInfo(msg: string) {
  console.log(`${colors.bgGray}[*]${colors.reset} ${msg}`);
}

export function logError(msg: string) {
  console.log(`${colors.bgRed}[ERROR]${colors.reset} ${msg}`);
}

export function logCreated(msg: string) {
  console.log(`${colors.bgBlue}[CREATED]${colors.reset} ${msg}`);
}

export function logSuccess(msg: string) {
  console.log(`${colors.bgGreen}[OK]${colors.reset} ${msg}`);
}
