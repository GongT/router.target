// todo: how add to tsc?
declare module '*.scss' {
	export interface IStyleSheet {
		style: string;
		scope: string;
	}

	const css: IStyleSheet;
	export default css;
}
