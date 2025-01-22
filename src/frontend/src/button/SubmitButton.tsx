// SubmitButton.tsx
import classNames from 'classnames';

type SubmitButtonProps = {
  isLoading: boolean;
  xl?: boolean;
  children: string;
};

const SubmitButton = ({ isLoading, xl, children }: SubmitButtonProps) => {
  const btnClass = classNames({
    'btn-base': true,
    'btn-xl': xl,
    'btn-primary': true,
    'btn-disabled': isLoading,
  });

  return (
    <button className={btnClass} disabled={isLoading}>
      {children}

      <style jsx>{`
        .btn-base {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
        }
        .btn-xl {
          padding: 12px 24px;
          font-size: 20px;
        }
        .btn-primary {
          background-color: #BD3432;
          color: white;
        }
        .btn-disabled {
          background-color: #ccc;
          color: #666;
          cursor: not-allowed;
        }
        .btn-primary:hover:not(.btn-disabled) {
          background-color: #DC0303;
        }
      `}</style>
    </button>
  );
};

export default SubmitButton;
