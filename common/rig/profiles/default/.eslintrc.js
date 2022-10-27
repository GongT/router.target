// This is a workaround for https://github.com/eslint/eslint/issues/3458
require('@rushstack/eslint-config/patch/modern-module-resolution');

const { createRequire } = require('module');
const { resolve, dirname } = require('path');

const isModuleResolutionError = (ex) =>
	typeof ex === 'object' && !!ex && 'code' in ex && ex.code === 'MODULE_NOT_FOUND';

function resolveESLintrcPackage() {
	try {
		let req;
		if (require.main?.filename) {
			req = createRequire(require.main?.filename);
		} else {
			req = require;
		}

		const eslintCli = req.resolve('eslint/package.json');
		console.log('ESLint is %s', dirname(eslintCli));

		const eslintRc = createRequire(eslintCli).resolve('@eslint/eslintrc');
		console.log('ESLintRC is %s', eslintRc);

		return require(eslintRc);
	} catch (e) {
		if (isModuleResolutionError(e)) {
			console.error('没有找到ESLint@8的正常依赖，请确定所有依赖包已正确安装');
			throw e;
		}
		throw e;
	}
}

function patchESLintResolver() {
	const exports = resolveESLintrcPackage();
	const ModuleResolver = exports.Legacy.ModuleResolver;

	const originalResolve = ModuleResolver.resolve;
	ModuleResolver.resolve = function hackedModuleResolver(name) {
		try {
			return originalResolve.apply(this, arguments);
		} catch (e) {
			if (!isModuleResolutionError(e)) {
				throw e;
			}

			// console.log('handle missing: ', name);
			return require.resolve(name);
		}
	};
}

patchESLintResolver();

module.exports = function loadConfig(__dirname) {
	const ret = {
		root: true,
		plugins: ['import'],
		parserOptions: {
			tsconfigRootDir: resolve(__dirname, 'src'),
			project: ['./tsconfig.json'],
		},
		ignorePatterns: ['**/*.js'],
		extends: [
			'@rushstack/eslint-config/profile/web-app',
			'@rushstack/eslint-config/mixins/friendly-locals',
			'@rushstack/eslint-config/mixins/react',
			'plugin:import/recommended',
			'plugin:import/typescript',
		],
		rules: {
			'import/no-default-export': 1,
			'@typescript-eslint/explicit-function-return-type': 0,
			'@typescript-eslint/typedef': 0,
			'@typescript-eslint/no-explicit-any': 0,
		},
	};

	return ret;
};
