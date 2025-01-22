import type { ReactNode } from 'react';

type ICTABannerProps = {
  title: string;
  button: ReactNode;
};

const CTABanner = (props: ICTABannerProps) => (
  <div className="flex flex-col rounded-md bg-primary-200 p-4 text-center sm:flex-row sm:items-center sm:justify-between sm:p-12 sm:text-left">
    <div className="text-2xl font-semibold">
      <div className="text-gray-900">{props.title}</div>
    </div>

    <div className="whitespace-no-wrap mt-3 sm:ml-2 sm:mt-0">
      {props.button}
    </div>
  </div>
);

export { CTABanner };
