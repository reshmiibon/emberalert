// opt in page
import Link from 'next/link';

import { Footer } from '@/templates/Footer';

import { Section } from '../layout/Section';
import { NavbarTwoColumns } from '../navigation/NavbarTwoColumns';
import { Logo } from '../templates/Logo';
import { OptInForm } from '../templates/OptInForm';

const OptIn = () => (
  <>
    <Section yPadding="py-6">
      <NavbarTwoColumns logo={<Logo xl />}>
        <li>
          <Link href="/map">Maps</Link>
        </li>
        <li>
          <Link href="/optin">Opt In</Link>
        </li>
      </NavbarTwoColumns>
    </Section>
    <div style={{ margin: '150px 0' }}></div>
    <OptInForm />;<div style={{ margin: '150px 0' }}></div>
    <Footer />
  </>
);
export default OptIn;
