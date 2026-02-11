// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	site: 'https://kamuyin.github.io/ipygame/',
	base: '/ipygame/',
	integrations: [
		starlight({
			title: 'ipygame',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/Kamuyin/ipygame' }],
			sidebar: [
				{
					label: 'Quick Start',
					link: 'quickstart',
				},
				{
					label: 'Examples',
					link: 'examples',
				},
				{
					label: 'API Coverage',
					link: 'api_coverage',
				},
				{
					label: 'API Reference',
					autogenerate: { directory: 'api' },
				},
			],
		}),
	],
});
